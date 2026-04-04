#!/usr/bin/env python3
"""
grace_gradio_fullbrain.py  —  GRACE Full-Brain Gradio Interface
Updated: Robot-style cyan O-ring eyes + animated mouth face
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

# ── FACE HTML — iframe with srcdoc (robot cyan O-ring eyes) ──────────────────

_IFRAME_DOC = """<!DOCTYPE html>
<html><head><style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#050508;overflow:hidden;width:100%;height:100%}
canvas{display:block;width:100%;height:100%}
</style></head><body>
<canvas id="c"></canvas>
<script>
var canvas=document.getElementById('c');
var ctx=canvas.getContext('2d');
var emotion='serene', speaking=false;
var W=0,H=0,blinkT=0,lastBlink=Date.now();
var curProps={},mouseX=.5,mouseY=.5,eyeLX=0,eyeLY=0,eyeRX=0,eyeRY=0;

function resize(){W=window.innerWidth||600;H=window.innerHeight||350;canvas.width=W;canvas.height=H;}
resize();
window.addEventListener('resize',resize);
window.addEventListener('message',function(e){
  var d=e.data||{};
  if(d.emotion) emotion=d.emotion.toLowerCase();
  if(d.speaking!==undefined) speaking=d.speaking;
});
document.addEventListener('mousemove',function(e){mouseX=e.clientX/W;mouseY=e.clientY/H;});

var EMOTIONS={
  serene:   {eyeOuter:38,eyeInner:22,eyeRing:2,mouthW:55,mouthH:6, mouthOpen:0,pupilSize:10,browAngle:0,   glowA:.7},
  happy:    {eyeOuter:36,eyeInner:20,eyeRing:2,mouthW:70,mouthH:10,mouthOpen:0,pupilSize:9, browAngle:-.08,glowA:1.0},
  sad:      {eyeOuter:34,eyeInner:19,eyeRing:2,mouthW:45,mouthH:6, mouthOpen:0,pupilSize:9, browAngle:.15, glowA:.4},
  surprised:{eyeOuter:46,eyeInner:28,eyeRing:3,mouthW:30,mouthH:8, mouthOpen:1,pupilSize:7, browAngle:-.15,glowA:1.0},
  thinking: {eyeOuter:32,eyeInner:16,eyeRing:2,mouthW:42,mouthH:4, mouthOpen:0,pupilSize:10,browAngle:.1,  glowA:.5},
  angry:    {eyeOuter:34,eyeInner:20,eyeRing:2,mouthW:50,mouthH:5, mouthOpen:0,pupilSize:8, browAngle:.25, glowA:.8},
  confused: {eyeOuter:36,eyeInner:21,eyeRing:2,mouthW:44,mouthH:5, mouthOpen:0,pupilSize:10,browAngle:.12, glowA:.55},
  curiosity:{eyeOuter:40,eyeInner:24,eyeRing:2,mouthW:50,mouthH:7, mouthOpen:0,pupilSize:10,browAngle:-.05,glowA:.8},
};
(function(){var e=EMOTIONS.serene;for(var k in e)curProps[k]=e[k];})();

function lerp(a,b,t){return a+(b-a)*t;}

function drawRobotEye(cx,cy,p,side,blinkScale){
  var outerR=p.eyeOuter,innerR=p.eyeInner,gA=p.glowA;
  var px=(mouseX-.5)*16*side,py=(mouseY-.5)*12;
  if(side===1){eyeLX=lerp(eyeLX,px,.08);eyeLY=lerp(eyeLY,py,.08);}
  else{eyeRX=lerp(eyeRX,px,.08);eyeRY=lerp(eyeRY,py,.08);}
  var ex=side===1?eyeLX:eyeRX,ey=side===1?eyeLY:eyeRY;
  ctx.save();ctx.translate(cx,cy);ctx.scale(1,blinkScale);
  ctx.beginPath();ctx.arc(0,0,outerR+8,0,Math.PI*2);
  ctx.fillStyle='rgba(0,8,20,.95)';ctx.fill();
  ctx.strokeStyle='rgba(0,200,255,.35)';ctx.lineWidth=1.5;ctx.stroke();
  var grd=ctx.createRadialGradient(0,0,innerR*.5,0,0,outerR+10);
  grd.addColorStop(0,'rgba(0,255,255,'+(gA*.25)+')');
  grd.addColorStop(1,'rgba(0,255,255,0)');
  ctx.beginPath();ctx.arc(0,0,outerR+10,0,Math.PI*2);ctx.fillStyle=grd;ctx.fill();
  ctx.beginPath();ctx.arc(0,0,outerR,0,Math.PI*2);
  ctx.strokeStyle='rgba(0,255,255,'+gA+')';ctx.lineWidth=p.eyeRing+1;
  ctx.shadowColor='rgba(0,255,255,'+(gA*.8)+')';ctx.shadowBlur=12;
  ctx.stroke();ctx.shadowBlur=0;
  ctx.beginPath();ctx.arc(0,0,innerR,0,Math.PI*2);
  ctx.fillStyle='rgba(0,8,20,.97)';ctx.fill();
  ctx.strokeStyle='rgba(0,200,255,'+(gA*.5)+')';ctx.lineWidth=1;ctx.stroke();
  var ps=p.pupilSize;
  ctx.beginPath();ctx.arc(ex*.6,ey*.6,ps,0,Math.PI*2);
  ctx.fillStyle='rgba(0,255,255,'+(gA*.9)+')';
  ctx.shadowColor='rgba(0,255,255,1)';ctx.shadowBlur=8;ctx.fill();ctx.shadowBlur=0;
  ctx.beginPath();ctx.arc(ex*.6-ps*.35,ey*.6-ps*.35,ps*.3,0,Math.PI*2);
  ctx.fillStyle='rgba(255,255,255,.9)';ctx.fill();
  ctx.restore();
}

function drawBrows(p){
  var cx=W/2,cy=H*.38,span=58,angle=p.browAngle,gA=p.glowA;
  ctx.strokeStyle='rgba(0,220,255,'+(gA*.7)+')';ctx.lineWidth=2.5;ctx.lineCap='round';
  ctx.save();ctx.translate(cx-span,cy-p.eyeOuter-10);ctx.rotate(-angle);
  ctx.beginPath();ctx.moveTo(-14,-4);ctx.lineTo(14,4);ctx.stroke();ctx.restore();
  ctx.save();ctx.translate(cx+span,cy-p.eyeOuter-10);ctx.rotate(angle);
  ctx.beginPath();ctx.moveTo(-14,4);ctx.lineTo(14,-4);ctx.stroke();ctx.restore();
}

function drawMouth(cx,cy,p){
  var w=p.mouthW,h=p.mouthH,gA=p.glowA;
  ctx.save();ctx.translate(cx,cy);
  var speakBob=speaking?Math.abs(Math.sin(Date.now()/70))*18:0;
  var mh=h+(speaking?speakBob*.4:0);
  if(ctx.roundRect){
    ctx.beginPath();ctx.roundRect(-w/2-4,-mh/2-4,w+8,mh+8,4);
  } else {
    ctx.beginPath();ctx.rect(-w/2-4,-mh/2-4,w+8,mh+8);
  }
  ctx.fillStyle='rgba(0,8,18,.9)';ctx.fill();
  ctx.strokeStyle='rgba(0,180,220,.3)';ctx.lineWidth=1;ctx.stroke();
  if(speaking){
    var bars=5;
    for(var i=0;i<bars;i++){
      var bh=4+Math.abs(Math.sin(Date.now()/60+i*1.1))*mh*.8;
      var bx=-w/2+i*(w/(bars-1));
      var alpha=gA*(.5+Math.abs(Math.sin(Date.now()/60+i*1.1))*.5);
      ctx.beginPath();
      if(ctx.roundRect){ctx.roundRect(bx-3,-bh/2,6,bh,2);}
      else{ctx.rect(bx-3,-bh/2,6,bh);}
      ctx.fillStyle='rgba(0,255,255,'+alpha+')';
      ctx.shadowColor='rgba(0,255,255,.6)';ctx.shadowBlur=6;ctx.fill();ctx.shadowBlur=0;
    }
  } else if(emotion==='happy'){
    ctx.beginPath();ctx.moveTo(-w/2,0);ctx.quadraticCurveTo(0,mh+6,w/2,0);
    ctx.strokeStyle='rgba(0,255,255,'+gA+')';ctx.lineWidth=2.5;ctx.lineCap='round';
    ctx.shadowColor='rgba(0,255,255,.6)';ctx.shadowBlur=8;ctx.stroke();ctx.shadowBlur=0;
  } else if(emotion==='sad'){
    ctx.beginPath();ctx.moveTo(-w/2,6);ctx.quadraticCurveTo(0,-mh-4,w/2,6);
    ctx.strokeStyle='rgba(0,200,255,'+(gA*.7)+')';ctx.lineWidth=2.5;ctx.lineCap='round';ctx.stroke();
  } else if(emotion==='surprised'){
    ctx.beginPath();ctx.arc(0,0,w/3,0,Math.PI*2);
    ctx.strokeStyle='rgba(0,255,255,'+gA+')';ctx.lineWidth=2;
    ctx.shadowColor='rgba(0,255,255,.5)';ctx.shadowBlur=6;ctx.stroke();ctx.shadowBlur=0;
  } else {
    ctx.beginPath();ctx.moveTo(-w/2,0);ctx.lineTo(w/2,0);
    ctx.strokeStyle='rgba(0,255,255,'+gA+')';ctx.lineWidth=2.5;ctx.lineCap='round';
    ctx.shadowColor='rgba(0,255,255,.5)';ctx.shadowBlur=6;ctx.stroke();ctx.shadowBlur=0;
  }
  ctx.restore();
}

function animate(){
  var now=Date.now();
  if(now-lastBlink>3500+Math.random()*3000){blinkT=1;lastBlink=now;}
  if(blinkT>0)blinkT=Math.max(0,blinkT-.065);
  var blinkScale=1-Math.sin(blinkT*Math.PI)*.95;
  var tgt=EMOTIONS[emotion]||EMOTIONS.serene;
  for(var k in tgt)curProps[k]=lerp(curProps[k]||tgt[k],tgt[k],.07);
  var p=curProps;
  ctx.fillStyle='#050508';ctx.fillRect(0,0,W,H);
  ctx.fillStyle='rgba(0,255,255,.012)';
  for(var y=0;y<H;y+=3)ctx.fillRect(0,y,W,1);
  ctx.strokeStyle='rgba(0,255,255,.025)';ctx.lineWidth=.5;
  for(var x=0;x<W;x+=50){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,H);ctx.stroke();}
  for(var yy=0;yy<H;yy+=50){ctx.beginPath();ctx.moveTo(0,yy);ctx.lineTo(W,yy);ctx.stroke();}
  var cx=W/2,ey=H*.38,span=58;
  drawBrows(p);
  drawRobotEye(cx-span,ey,p,1,blinkScale);
  drawRobotEye(cx+span,ey,p,-1,blinkScale);
  drawMouth(cx,ey+p.eyeOuter+42,p);
  ctx.font='11px monospace';ctx.fillStyle='rgba(0,255,255,.4)';
  ctx.textAlign='center';ctx.fillText(emotion.toUpperCase(),W/2,H-12);
  requestAnimationFrame(animate);
}
animate();
</script>
</body></html>"""

_SRCDOC = _IFRAME_DOC.replace('"', '&quot;')

FACE_HTML = (
    f'<iframe id="grace-face-iframe" srcdoc="{_SRCDOC}" '
    f'style="width:100%;height:350px;border:none;border-radius:12px;display:block;" '
    f'sandbox="allow-scripts">'
    f'</iframe>'
)

PARENT_INIT_JS = """
() => {
    window.updateGraceEmotion = function(emotion) {
        var f = document.getElementById('grace-face-iframe');
        if (f && f.contentWindow) f.contentWindow.postMessage({emotion: emotion}, '*');
    };
    window.setGraceSpeaking = function(speaking) {
        var f = document.getElementById('grace-face-iframe');
        if (f && f.contentWindow) f.contentWindow.postMessage({speaking: speaking}, '*');
    };
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
<span class="metric-pill"><span class="emotion-badge">{s.emotion}</span></span>
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
    js=("if(window.updateGraceEmotion)window.updateGraceEmotion('thinking');"
        "if(window.setGraceSpeaking)window.setGraceSpeaking(true);")
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