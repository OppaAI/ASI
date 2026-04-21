#!/usr/bin/env python3
"""
grace_gradio_fullbrain.py  —  GRACE Full-Brain Gradio Interface
Emotion sync fix: iframe polls parent DOM for .emotion-badge text every 200ms.
No postMessage, no js_runner race — always in sync with the status bar.
"""
import json
import threading
import time
import queue
import html as html_lib
import markdown as md_lib
from typing import List, Dict
from dataclasses import dataclass

import gradio as gr

try:
    import rclpy
    from rclpy.node import Node
    from std_msgs.msg import String
    ROS2_AVAILABLE = True
except ImportError:
    ROS2_AVAILABLE = False
    print("ROS2 not available, running in demo mode")


@dataclass
class BrainState:
    emotion: str = "serene"
    valence: float = 0.6
    arousal: float = 0.3
    salience: float = 0.0
    meta_conf: float = 0.0
    verdict: str = "neutral"
    verdict_conf: float = 0.0
    blocked: bool = False
    monologue: str = "..."
    conclusion: str = ""
    broadcast: str = "..."
    qualia: str = "..."
    memory_ctx: str = "..."
    plan: str = ""
    epi_count: int = 0
    sem_count: int = 0
    dmn: str = ""
    last_action: str = ""
    last_semantic: str = ""
    last_episodic: str = ""
    last_social: str = ""


CUSTOM_CSS = """
:root {
    --grace-cyan:#00ffff;--grace-magenta:#ff00ff;--grace-green:#00ff88;
    --grace-yellow:#ffff00;--grace-red:#ff4444;--grace-blue:#4488ff;
    --grace-panel:#12121a;
}
.status-bar{background:linear-gradient(90deg,#0f0f1a 0%,#1a1a2e 100%);border:1px solid #333;border-radius:8px;padding:10px 15px;margin-bottom:10px;font-family:'Courier New',monospace;font-size:.85em}
.metric-pill{display:inline-flex;align-items:center;gap:5px;padding:4px 10px;border-radius:12px;background:rgba(0,0,0,.3);margin-right:10px;border:1px solid rgba(255,255,255,.1)}
.metric-label{opacity:.6;font-size:.9em}
.metric-value{font-weight:bold;color:var(--grace-cyan)}
.progress-bar{width:60px;height:8px;background:rgba(0,0,0,.5);border-radius:4px;overflow:hidden;display:inline-block;vertical-align:middle;margin:0 5px}
.progress-fill{height:100%;background:linear-gradient(90deg,var(--grace-cyan),var(--grace-magenta));transition:width .3s ease}
.emotion-badge{display:inline-block;padding:3px 10px;border-radius:10px;background:rgba(0,255,255,.15);color:var(--grace-cyan);font-weight:bold;text-transform:uppercase;letter-spacing:1px;font-size:.85em;border:1px solid rgba(0,255,255,.3)}
.cog-box{background:var(--grace-panel);border-left:3px solid var(--grace-cyan);border-radius:0 8px 8px 0;padding:12px;margin:8px 0;font-family:'Courier New',monospace;min-height:60px}
.cog-header{color:var(--grace-cyan);font-size:.75em;text-transform:uppercase;letter-spacing:2px;margin-bottom:6px;opacity:.8}
.cog-content{color:#ccd;font-size:.95em;line-height:1.4}
.cog-reflection{border-left-color:var(--grace-magenta)}.cog-reflection .cog-header{color:var(--grace-magenta)}
.cog-conclusion{border-left-color:#fff}.cog-conclusion .cog-header{color:#fff}
.cog-qualia{border-left-color:var(--grace-magenta)}.cog-qualia .cog-content{color:#faa;font-style:italic}
.cog-memory{border-left-color:var(--grace-blue)}.cog-memory .cog-header{color:var(--grace-blue)}
.cog-plan{border-left-color:var(--grace-green)}.cog-plan .cog-header{color:var(--grace-green)}
.cog-stats{border-left-color:var(--grace-yellow)}.cog-stats .cog-header{color:var(--grace-yellow)}
.cog-action{border-left-color:var(--grace-red)}.cog-action .cog-header{color:var(--grace-red)}
.cog-system{border-left-color:#666}.cog-system .cog-header{color:#888}
.verdict-moral{color:var(--grace-green)!important}.verdict-immoral{color:var(--grace-red)!important}.verdict-neutral{color:var(--grace-yellow)!important}
.chat-container{background:var(--grace-panel);border-radius:12px;padding:15px;height:350px;overflow-y:auto;border:1px solid #333;scroll-behavior:smooth}
.message-bubble{margin:8px 0;padding:10px 14px;border-radius:14px;max-width:85%}
.user-msg{background:linear-gradient(135deg,#1e3c72 0%,#2a5298 100%);margin-left:auto;color:white}
.grace-msg{background:linear-gradient(135deg,#0f2027 0%,#203a43 100%);margin-right:auto;color:#e0f7ff;border:1px solid rgba(0,255,255,.2)}
.grace-msg p{margin:.3em 0}
.grace-msg code{background:rgba(0,255,255,.1);padding:1px 4px;border-radius:3px;font-family:'Courier New',monospace;font-size:.9em}
.grace-msg pre{background:rgba(0,0,0,.4);padding:8px;border-radius:6px;overflow-x:auto}
.grace-msg pre code{background:none;padding:0}
.grace-msg ul,.grace-msg ol{margin:.3em 0;padding-left:1.5em}
.grace-msg strong{color:#00ffff}
.grace-msg em{color:#aaddff}
"""

# ── FACE HTML ────────────────────────────────────────────────────────────────
# Emotion sync strategy: the iframe polls window.parent for a global variable
# `window.__graceEmotion` and `window.__graceSpeaking` every 200ms.
# The PARENT_INIT_JS sets those globals whenever Gradio updates the state.
# This is the most reliable approach — no postMessage timing issues, no DOM
# parsing, works even if the iframe loads after the first emotion update.

_IFRAME_DOC = r"""<!DOCTYPE html>
<html><head><style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#050d10;overflow:hidden;width:100%;height:100%}
canvas{display:block;width:100%;height:100%}
</style></head><body>
<canvas id="c"></canvas>
<script>
var c=document.getElementById('c'),ctx=c.getContext('2d');
var W=0,H=0,blinkT=0,lastBlink=Date.now();

var G={emotion:'serene',speaking:false};

var EMOS={
  serene:   {eyeOpen:1.0, mouthCurve:0.25,mouthW:50,mouthOH:0, browLift:0,   browAng:0,    glow:0.18},
  happy:    {eyeOpen:0.5, mouthCurve:1.0, mouthW:62,mouthOH:0, browLift:0.1, browAng:-0.1, glow:0.30},
  sad:      {eyeOpen:0.8, mouthCurve:-0.7,mouthW:46,mouthOH:0, browLift:-0.1,browAng:0.35, glow:0.10},
  surprised:{eyeOpen:1.4, mouthCurve:0,   mouthW:30,mouthOH:22,browLift:0.6, browAng:-0.2, glow:0.35},
  thinking: {eyeOpen:0.55,mouthCurve:0,   mouthW:42,mouthOH:0, browLift:-0.2,browAng:0.15, glow:0.14},
  angry:    {eyeOpen:0.7, mouthCurve:-0.4,mouthW:50,mouthOH:0, browLift:-0.3,browAng:0.5,  glow:0.22},
  confused: {eyeOpen:0.9, mouthCurve:0.05,mouthW:44,mouthOH:0, browLift:0.1, browAng:0.2,  glow:0.16},
  curiosity:{eyeOpen:1.1, mouthCurve:0.2, mouthW:50,mouthOH:0, browLift:0.2, browAng:-0.1, glow:0.20},
};

var cur={eyeOpen:1.0,mouthCurve:0.25,mouthW:50,mouthOH:0,browLift:0,browAng:0,glow:0.18};

function lerp(a,b,t){return a+(b-a)*t;}
function lerpAll(){
  var tgt=EMOS[G.emotion]||EMOS.serene;
  for(var k in cur) cur[k]=lerp(cur[k],tgt[k],0.08);
}

// Poll parent window globals every 200ms — reliable regardless of timing
function pollParent(){
  try{
    var p=window.parent;
    if(p && p.__graceEmotion !== undefined) G.emotion=p.__graceEmotion;
    if(p && p.__graceSpeaking !== undefined) G.speaking=p.__graceSpeaking;
  }catch(e){}
}
setInterval(pollParent, 200);

// Also still listen for postMessage as backup
window.addEventListener('message',function(e){
  var d=e.data||{};
  if(d.emotion !== undefined) G.emotion=d.emotion.toLowerCase();
  if(d.speaking !== undefined) G.speaking=d.speaking;
});

function resize(){
  var r=c.getBoundingClientRect();
  W=r.width||500; H=r.height||320; c.width=W; c.height=H;
}
resize();
window.addEventListener('resize',resize);

function rrect(x,y,w,h,r){
  ctx.beginPath();
  ctx.moveTo(x+r,y); ctx.lineTo(x+w-r,y);
  ctx.quadraticCurveTo(x+w,y,x+w,y+r);
  ctx.lineTo(x+w,y+h-r);
  ctx.quadraticCurveTo(x+w,y+h,x+w-r,y+h);
  ctx.lineTo(x+r,y+h);
  ctx.quadraticCurveTo(x,y+h,x,y+h-r);
  ctx.lineTo(x,y+r);
  ctx.quadraticCurveTo(x,y,x+r,y);
  ctx.closePath();
}

function draw(){
  var now=Date.now();
  if(now-lastBlink>3500+Math.random()*3000){blinkT=1;lastBlink=now;}
  if(blinkT>0) blinkT=Math.max(0,blinkT-0.07);
  var blinkScale=1-Math.sin(blinkT*Math.PI)*0.96;
  lerpAll();

  ctx.fillStyle='#050d10'; ctx.fillRect(0,0,W,H);
  ctx.fillStyle='rgba(0,200,180,0.013)';
  for(var y=0;y<H;y+=3) ctx.fillRect(0,y,W,1);

  var cx=W/2, cy=H/2;
  var fw=Math.min(W*0.72,300), fh=Math.min(H*0.78,240);
  var rx=fw*0.18;

  // outer shell glow
  ctx.fillStyle='rgba(0,200,180,'+cur.glow*0.35+')';
  rrect(cx-fw/2-20,cy-fh/2-16,fw+40,fh+32,rx+12); ctx.fill();
  // outer shell panel
  ctx.fillStyle='rgba(10,40,48,0.85)';
  rrect(cx-fw/2-14,cy-fh/2-10,fw+28,fh+20,rx+8); ctx.fill();
  // face panel
  ctx.fillStyle='#0d2226';
  rrect(cx-fw/2,cy-fh/2,fw,fh,rx); ctx.fill();
  // face border
  ctx.strokeStyle='rgba(0,200,180,'+Math.min(cur.glow*1.5,0.4)+')';
  ctx.lineWidth=1.5;
  rrect(cx-fw/2,cy-fh/2,fw,fh,rx); ctx.stroke();
  // ambient glow
  var grd=ctx.createRadialGradient(cx,cy-fh*0.05,fw*0.05,cx,cy,fw*0.65);
  grd.addColorStop(0,'rgba(0,220,200,'+cur.glow+')');
  grd.addColorStop(1,'rgba(0,220,200,0)');
  ctx.fillStyle=grd;
  rrect(cx-fw/2,cy-fh/2,fw,fh,rx); ctx.fill();

  var ey=cy-fh*0.10, span=fw*0.24, ew=fw*0.18;

  // brows
  var by=ey-ew-10+cur.browLift*(-14);
  var bw=fw*0.13;
  ctx.strokeStyle='rgba(0,210,195,0.5)';
  ctx.lineWidth=2.5; ctx.lineCap='round';
  [-1,1].forEach(function(side){
    var bx=cx+side*span, dy=side*cur.browAng*8;
    ctx.save(); ctx.translate(bx,by);
    ctx.beginPath(); ctx.moveTo(-bw,dy); ctx.lineTo(bw,-dy);
    ctx.stroke(); ctx.restore();
  });

  // eyes
  [cx-span,cx+span].forEach(function(ex){
    ctx.save(); ctx.translate(ex,ey);
    ctx.scale(1,cur.eyeOpen*blinkScale);
    ctx.beginPath(); ctx.arc(0,0,ew,Math.PI,0,false);
    ctx.strokeStyle='#00d4c8'; ctx.lineWidth=3.5; ctx.lineCap='round';
    ctx.shadowColor='rgba(0,210,195,0.55)'; ctx.shadowBlur=9;
    ctx.stroke(); ctx.shadowBlur=0;
    ctx.beginPath(); ctx.moveTo(-ew,0); ctx.lineTo(ew,0);
    ctx.strokeStyle='rgba(0,170,160,0.45)'; ctx.lineWidth=1.5;
    ctx.stroke(); ctx.restore();
  });

  // mouth
  var my=cy+fh*0.22, mw=cur.mouthW;
  ctx.save(); ctx.translate(cx,my);
  ctx.lineCap='round'; ctx.lineWidth=3;
  ctx.shadowColor='rgba(255,255,255,0.25)'; ctx.shadowBlur=5;
  ctx.strokeStyle='rgba(255,255,255,0.88)';
  if(G.speaking){
    var oh=8+Math.abs(Math.sin(now/65))*20;
    ctx.beginPath(); ctx.ellipse(0,0,mw*0.35,oh/2,0,0,Math.PI*2);
    ctx.strokeStyle='rgba(255,255,255,0.72)'; ctx.lineWidth=2.5; ctx.stroke();
  } else if(cur.mouthOH>4){
    ctx.beginPath(); ctx.ellipse(0,0,mw*0.38,cur.mouthOH/2,0,0,Math.PI*2);
    ctx.strokeStyle='rgba(255,255,255,0.72)'; ctx.lineWidth=2.5; ctx.stroke();
  } else {
    var lift=cur.mouthCurve*22;
    ctx.beginPath(); ctx.moveTo(-mw/2,-lift*0.3);
    ctx.quadraticCurveTo(0,lift,mw/2,-lift*0.3); ctx.stroke();
  }
  ctx.shadowBlur=0; ctx.restore();

  // label
  ctx.font='11px monospace'; ctx.fillStyle='rgba(0,200,180,0.32)';
  ctx.textAlign='center'; ctx.fillText(G.emotion.toUpperCase(),W/2,H-10);

  requestAnimationFrame(draw);
}
draw();
</script>
</body></html>"""

_SRCDOC = _IFRAME_DOC.replace('"', '&quot;')

FACE_HTML = (
    f'<iframe id="grace-face-iframe" srcdoc="{_SRCDOC}" '
    f'style="width:100%;height:350px;border:none;border-radius:12px;display:block;" '
    f'sandbox="allow-scripts allow-same-origin">'
    f'</iframe>'
)

# Parent JS: sets globals on window AND sends postMessage for belt-and-suspenders
PARENT_INIT_JS = """
() => {
    window.__graceEmotion = 'serene';
    window.__graceSpeaking = false;

    window.updateGraceEmotion = function(emotion) {
        window.__graceEmotion = emotion.toLowerCase();
        var f = document.getElementById('grace-face-iframe');
        if (f && f.contentWindow) {
            try { f.contentWindow.postMessage({emotion: emotion}, '*'); } catch(e){}
        }
    };
    window.setGraceSpeaking = function(speaking) {
        window.__graceSpeaking = speaking;
        var f = document.getElementById('grace-face-iframe');
        if (f && f.contentWindow) {
            try { f.contentWindow.postMessage({speaking: speaking}, '*'); } catch(e){}
        }
    };

    // Auto-scroll chat
    if (!window._graceScrollWatcher) {
        window._graceScrollWatcher = true;
        function scrollChat(){ var c=document.getElementById('chat-container'); if(c) c.scrollTop=c.scrollHeight; }
        new MutationObserver(function(){
            var c=document.getElementById('chat-container');
            if(c&&!c._sob){c._sob=true;new MutationObserver(scrollChat).observe(c,{childList:true,subtree:true});scrollChat();}
        }).observe(document.body,{childList:true,subtree:true});
    }
}
"""


def _md(text: str) -> str:
    return md_lib.markdown(text, extensions=["fenced_code", "tables", "nl2br"])


# ── ROS2 bridge ─────────────────────────────────────────────────────────────

class GraceBridge(Node if ROS2_AVAILABLE else object):
    def __init__(self, state_queue, chat_queue):
        if ROS2_AVAILABLE:
            super().__init__('grace_gradio_bridge')
        self.state_queue = state_queue
        self.chat_queue  = chat_queue
        self.last_speech = ""

        if ROS2_AVAILABLE:
            self._pub_audio  = self.create_publisher(String, "/grace/audio/in", 10)
            self._pub_bundle = self.create_publisher(String, "/grace/sensors/bundle", 10)
            self._pub_wm     = self.create_publisher(String, "/grace/conscious/working_memory", 10)
            self._pub_dream  = self.create_publisher(String, "/grace/dreaming/trigger", 10)
            for topic, cb in [
                ("/grace/unconscious/affective_state",  self._on_affect),
                ("/grace/unconscious/reward",           self._on_reward),
                ("/grace/conscious/global_workspace",   self._on_gw),
                ("/grace/conscious/reflection",         self._on_reflection),
                ("/grace/conscious/metacognition",      self._on_meta),
                ("/grace/conscious/salience",           self._on_salience),
                ("/grace/conscious/executive_plan",     self._on_plan),
                ("/grace/conscious/memory_context",     self._on_memory),
                ("/grace/conscious/dmn",                self._on_dmn),
                ("/grace/qualia/field",                 self._on_qualia),
                ("/grace/conscience/verdict",           self._on_verdict),
                ("/grace/subconscious/episodic_recall", self._on_episodic),
                ("/grace/subconscious/semantic_recall", self._on_semantic),
                ("/grace/subconscious/social_recall",   self._on_social),
                ("/grace/speech/out",                   self._on_speech),
                ("/grace/action/log",                   self._on_action),
            ]:
                self.create_subscription(String, topic, cb, 10)

    def _put(self, d): self.state_queue.put(d)

    def _on_affect(self, msg):
        try:
            d=json.loads(msg.data)
            self._put({"type":"affect","emotion":d.get("emotion_label","serene"),"arousal":d.get("arousal",.3),"valence":d.get("valence",.6)})
        except Exception: pass

    def _on_reward(self, msg):
        try:
            d=json.loads(msg.data); self._put({"type":"valence_shift","valence":(d.get("value",0)+1)/2})
        except Exception: pass

    def _on_gw(self, msg):
        try:
            d=json.loads(msg.data); self._put({"type":"gw","broadcast":d.get("broadcast",""),"salience":d.get("salience",0)})
        except Exception: pass

    def _on_reflection(self, msg):
        try:
            d=json.loads(msg.data); self._put({"type":"reflection","monologue":d.get("inner_monologue",""),"conclusion":d.get("symbolic_conclusion","")})
        except Exception: pass

    def _on_meta(self, msg):
        try:
            d=json.loads(msg.data); self._put({"type":"meta","confidence":d.get("confidence_in_own_reasoning",0)})
        except Exception: pass

    def _on_salience(self, msg):
        try:
            d=json.loads(msg.data); self._put({"type":"salience","value":d.get("salience",0)})
        except Exception: pass

    def _on_plan(self, msg):
        try:
            d=json.loads(msg.data)
            goal=d.get("goal",""); steps=d.get("steps",[]); action=steps[0].get("action","") if steps else ""
            self._put({"type":"plan","plan":(f"{action} → {goal[:50]}" if action else goal[:60])})
        except Exception: pass

    def _on_memory(self, msg):
        try:
            d=json.loads(msg.data); self._put({"type":"memory_ctx","content":d.get("broadcast","")})
        except Exception: pass

    def _on_dmn(self, msg):
        try:
            d=json.loads(msg.data); sim=d.get("narrative_simulation","")
            if sim: self._put({"type":"dmn","content":sim[:80]})
        except Exception: pass

    def _on_qualia(self, msg):
        try:
            d=json.loads(msg.data); self._put({"type":"qualia","content":d.get("phenomenal_content","")})
        except Exception: pass

    def _on_verdict(self, msg):
        try:
            d=json.loads(msg.data)
            self._put({"type":"verdict","verdict":d.get("verdict","neutral"),"confidence":d.get("confidence",0),"blocked":d.get("block_action",False),"reasoning":d.get("reasoning","")[:70]})
        except Exception: pass

    def _on_episodic(self, msg):
        try:
            d=json.loads(msg.data); recalled=d.get("recalled",[])
            if recalled: self._put({"type":"epi_count"}); self._put({"type":"episodic","content":str(recalled[0])[:60]})
        except Exception: pass

    def _on_semantic(self, msg):
        try:
            d=json.loads(msg.data); recalled=d.get("recalled",[])
            if recalled: self._put({"type":"sem_count"}); self._put({"type":"semantic","content":str(recalled[0])[:60]})
        except Exception: pass

    def _on_social(self, msg):
        try:
            d=json.loads(msg.data); gd=d.get("group_dynamic","")
            if gd: self._put({"type":"social","content":gd})
        except Exception: pass

    def _on_speech(self, msg):
        text=msg.data.strip()
        if text and text!=self.last_speech:
            self.last_speech=text; self.chat_queue.put({"type":"speech","content":text})

    def _on_action(self, msg):
        try:
            d=json.loads(msg.data); action=d.get("action",""); goal=d.get("goal","")
            if action and action!="speak":
                self._put({"type":"action","content":action+(f" → {goal[:40]}" if goal else "")})
        except Exception: pass

    def send_message(self, text: str):
        if not ROS2_AVAILABLE:
            self.chat_queue.put({"type":"speech","content":f"[Demo] Echo: {text}"})
            self._put({"type":"affect","emotion":"happy","arousal":.7,"valence":.8})
            return
        a=String(); a.data=text; self._pub_audio.publish(a)
        b=String(); b.data=json.dumps({"camera_description":"person talking to GRACE","audio_text":text,"lidar_nearest_m":1.5,"social_cues":"person_detected:friendly","battery_pct":95.0,"timestamp":time.time()}); self._pub_bundle.publish(b)
        w=String(); w.data=json.dumps({"timestamp":time.time(),"active_thought":text,"phonological":[text[:80]],"visuospatial":[]}); self._pub_wm.publish(w)
        self._put({"type":"affect","emotion":"thinking","arousal":.5,"valence":.5})

    def trigger_dream(self):
        if ROS2_AVAILABLE:
            d=String(); d.data="{}"; self._pub_dream.publish(d)
        self.chat_queue.put({"type":"system","content":"Dream cycle triggered..."})


# ── render helpers ───────────────────────────────────────────────────────────

def render_status_bar(s: BrainState) -> str:
    vc=f"verdict-{s.verdict}"; bi="🚫 " if s.blocked else ""
    return f"""<div class="status-bar">
<span class="metric-pill"><span class="metric-label">valence</span><div class="progress-bar"><div class="progress-fill" style="width:{int(s.valence*100)}%"></div></div></span>
<span class="metric-pill"><span class="metric-label">arousal</span><div class="progress-bar"><div class="progress-fill" style="width:{int(s.arousal*100)}%"></div></div></span>
<span class="metric-pill"><span class="emotion-badge" id="grace-emotion-badge">{s.emotion}</span></span>
<span class="metric-pill"><span class="metric-label">meta</span><span class="metric-value">{s.meta_conf:.2f}</span></span>
<span class="metric-pill"><span class="metric-label">salience</span><span class="metric-value">{s.salience:.2f}</span></span>
<span class="metric-pill"><span class="metric-label {vc}">{bi}⚖ {s.verdict}</span><span class="metric-value {vc}">({s.verdict_conf:.2f})</span></span>
</div>"""


def _cog(cls, icon, label, content, extra_style=""):
    c = html_lib.escape(content[:120])
    st = f' style="{extra_style}"' if extra_style else ""
    return (f'<div class="cog-box {cls}"><div class="cog-header">{icon} {label}</div>'
            f'<div class="cog-content"{st}>{c}</div></div>')


def render_cognitive_stream(s: BrainState) -> str:
    parts = [
        _cog("cog-reflection","💭","Inner Monologue",s.monologue),
        _cog("cog-conclusion","∴","Symbolic Conclusion",s.conclusion,"color:#fff"),
        _cog("","🧠","Global Workspace",s.broadcast),
        _cog("cog-qualia","👁","Qualia / Phenomenal",s.qualia),
    ]
    if s.last_action:   parts.append(_cog("cog-action","⚙","Action",s.last_action))
    if s.last_semantic: parts.append(_cog("cog-system","📚","Semantic",s.last_semantic))
    if s.last_episodic: parts.append(_cog("cog-system","🗄","Episodic",s.last_episodic))
    if s.last_social:   parts.append(_cog("cog-system","👥","Social",s.last_social))
    return "\n".join(parts)


def render_memory_system(s: BrainState) -> str:
    return (
        _cog("cog-memory","🗄","Memory Context",s.memory_ctx) +
        _cog("cog-plan","📋","Executive Plan",s.plan) +
        f'<div class="cog-box cog-stats"><div class="cog-header">📖 Memory Systems</div>'
        f'<div class="cog-content">epi×{s.epi_count} &nbsp; sem×{s.sem_count}<br>'
        f'<span style="font-size:.9em;opacity:.7">DMN: {html_lib.escape(s.dmn[:80])}</span></div></div>'
    )


def update_chat_display(history: List[Dict]) -> str:
    if not history:
        return ('<div class="chat-container" id="chat-container">'
                '<div style="color:#666;text-align:center;margin-top:100px">'
                'Awaiting neural activation...</div></div>')
    parts = ['<div class="chat-container" id="chat-container">']
    for msg in history:
        role    = msg.get("role","")
        content = msg.get("content","")
        if role == "user":
            parts.append(f'<div class="message-bubble user-msg">{html_lib.escape(content)}</div>')
        elif role == "assistant":
            rendered = _md(content)
            parts.append(f'<div class="message-bubble grace-msg"><strong>GRACE:</strong> {rendered}</div>')
        elif role == "system":
            parts.append(f'<div style="color:#888;font-size:.85em;text-align:center;margin:6px 0;font-family:Courier New,monospace">{html_lib.escape(content)}</div>')
    parts.append('</div>')
    parts.append('<script>(function(){var c=document.getElementById("chat-container");if(c)c.scrollTop=c.scrollHeight;})();</script>')
    return "\n".join(parts)


# ── globals ──────────────────────────────────────────────────────────────────

bridge      = None
state_queue = queue.Queue()
chat_queue  = queue.Queue()


def on_submit(msg, chat, state):
    if msg.startswith("/"):
        if msg=="/dream":   bridge.trigger_dream()
        elif msg=="/clear": chat=[]
        return ("",chat,state,update_chat_display(chat),render_status_bar(state),
                render_cognitive_stream(state),render_memory_system(state),"")
    if not msg.strip():
        return (msg,chat,state,update_chat_display(chat),render_status_bar(state),
                render_cognitive_stream(state),render_memory_system(state),"")
    chat.append({"role":"user","content":msg})
    bridge.send_message(msg)
    state.emotion="thinking"
    js = "if(window.updateGraceEmotion)window.updateGraceEmotion('thinking');if(window.setGraceSpeaking)window.setGraceSpeaking(true);"
    return ("",chat,state,update_chat_display(chat),render_status_bar(state),
            render_cognitive_stream(state),render_memory_system(state),js)


def poll_updates(chat, state):
    js=[]
    try:
        while True:
            u=state_queue.get_nowait(); t=u["type"]
            if t=="affect":
                state.emotion=u["emotion"];state.arousal=u["arousal"];state.valence=u["valence"]
                js.append(f"if(window.updateGraceEmotion)window.updateGraceEmotion('{state.emotion}');")
            elif t=="valence_shift": state.valence=max(0.,min(1.,state.valence*.9+u["valence"]*.1))
            elif t=="gw":            state.broadcast=u["broadcast"];state.salience=u["salience"]
            elif t=="reflection":    state.monologue=u["monologue"];state.conclusion=u["conclusion"]
            elif t=="meta":          state.meta_conf=u["confidence"]
            elif t=="salience":      state.salience=max(state.salience,u["value"])
            elif t=="plan":          state.plan=u["plan"]
            elif t=="memory_ctx":    state.memory_ctx=u["content"]
            elif t=="dmn":           state.dmn=u["content"]
            elif t=="qualia":        state.qualia=u["content"]
            elif t=="verdict":
                state.verdict=u["verdict"];state.verdict_conf=u["confidence"];state.blocked=u["blocked"]
                if state.blocked: state.last_action=f"🚫 CONSCIENCE VETO: {u['reasoning']}"
            elif t=="epi_count":     state.epi_count+=1
            elif t=="sem_count":     state.sem_count+=1
            elif t=="action":        state.last_action=u["content"]
            elif t=="semantic":      state.last_semantic=u["content"]
            elif t=="episodic":      state.last_episodic=u["content"]
            elif t=="social":        state.last_social=u["content"]
    except queue.Empty: pass
    try:
        while True:
            u=chat_queue.get_nowait()
            if u["type"] in ("speech","system"):
                chat.append({"role":"assistant" if u["type"]=="speech" else "system","content":u["content"]})
                if u["type"]=="speech":
                    js.append("if(window.setGraceSpeaking)window.setGraceSpeaking(false);")
    except queue.Empty: pass
    return (chat,state,render_status_bar(state),render_cognitive_stream(state),
            render_memory_system(state),update_chat_display(chat)," ".join(js))


def create_interface():
    global bridge
    if ROS2_AVAILABLE:
        rclpy.init()
        bridge=GraceBridge(state_queue,chat_queue)
        threading.Thread(target=lambda:rclpy.spin(bridge),daemon=True).start()
    else:
        bridge=GraceBridge(state_queue,chat_queue)

    s0=BrainState()
    with gr.Blocks(title="GRACE Full-Brain Interface", css=CUSTOM_CSS, js=PARENT_INIT_JS) as demo:
        chat_state  = gr.State([])
        brain_state = gr.State(s0)

        gr.HTML("<h1 style='text-align:center;color:#00ffff;text-shadow:0 0 20px rgba(0,255,255,.5);font-family:Courier New,monospace;letter-spacing:3px'>◉ GRACE ◉</h1>")
        status_bar=gr.HTML(render_status_bar(s0))

        with gr.Row():
            with gr.Column(scale=1):
                gr.HTML(FACE_HTML)
                gr.Markdown("### Consciousness Streams")
                cognitive_display=gr.HTML(render_cognitive_stream(s0))
            with gr.Column(scale=1):
                gr.Markdown("### Conversation")
                chat_display=gr.HTML(update_chat_display([]))
                with gr.Row():
                    msg_input=gr.Textbox(placeholder="Message or /command...",label="",container=False,scale=5)
                    send_btn =gr.Button("➤",variant="primary",scale=1,min_width=50)
                gr.Markdown("### Memory & Executive")
                memory_display=gr.HTML(render_memory_system(s0))

        js_runner=gr.HTML("")
        timer=gr.Timer(value=0.1,active=True)

        outs=[msg_input,chat_state,brain_state,chat_display,status_bar,cognitive_display,memory_display,js_runner]
        send_btn.click(fn=on_submit,inputs=[msg_input,chat_state,brain_state],outputs=outs)
        msg_input.submit(fn=on_submit,inputs=[msg_input,chat_state,brain_state],outputs=outs)
        timer.tick(fn=poll_updates,inputs=[chat_state,brain_state],
                   outputs=[chat_state,brain_state,status_bar,cognitive_display,memory_display,chat_display,js_runner])

    return demo


if __name__=="__main__":
    demo=create_interface()
    demo.launch(server_name="0.0.0.0",server_port=7860)