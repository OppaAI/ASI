#!/usr/bin/env python3
"""
grace_gradio_fullbrain.py
Full-brain Gradio interface for GRACE - FIXED VERSION
"""
import json
import threading
import time
import queue
from typing import Tuple, List, Dict
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

FACE_HTML = """
<div id="face-container" style="background: #000; width: 100%; height: 350px; position: relative; overflow: hidden; border-radius: 12px; box-shadow: inset 0 0 60px rgba(0,255,255,0.1); border: 1px solid #333;">
    <canvas id="faceCanvas" style="display: block; width: 100%; height: 100%;"></canvas>
</div>
"""

CUSTOM_CSS = """
:root { --grace-cyan: #00ffff; --grace-magenta: #ff00ff; --grace-green: #00ff88; --grace-yellow: #ffff00; --grace-red: #ff4444; --grace-blue: #4488ff; --grace-bg: #0a0a0f; --grace-panel: #12121a; }
.status-bar { background: linear-gradient(90deg, #0f0f1a 0%, #1a1a2e 100%); border: 1px solid #333; border-radius: 8px; padding: 10px 15px; margin-bottom: 10px; font-family: 'Courier New', monospace; font-size: 0.85em; }
.metric-pill { display: inline-flex; align-items: center; gap: 5px; padding: 4px 10px; border-radius: 12px; background: rgba(0,0,0,0.3); margin-right: 10px; border: 1px solid rgba(255,255,255,0.1); }
.metric-label { opacity: 0.6; font-size: 0.9em; }
.metric-value { font-weight: bold; color: var(--grace-cyan); }
.progress-bar { width: 60px; height: 8px; background: rgba(0,0,0,0.5); border-radius: 4px; overflow: hidden; display: inline-block; vertical-align: middle; margin: 0 5px; }
.progress-fill { height: 100%; background: linear-gradient(90deg, var(--grace-cyan), var(--grace-magenta)); transition: width 0.3s ease; }
.emotion-badge { display: inline-block; padding: 3px 10px; border-radius: 10px; background: rgba(0,255,255,0.15); color: var(--grace-cyan); font-weight: bold; text-transform: uppercase; letter-spacing: 1px; font-size: 0.85em; border: 1px solid rgba(0,255,255,0.3); }
.cog-box { background: var(--grace-panel); border-left: 3px solid var(--grace-cyan); border-radius: 0 8px 8px 0; padding: 12px; margin: 8px 0; font-family: 'Courier New', monospace; min-height: 60px; }
.cog-header { color: var(--grace-cyan); font-size: 0.75em; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 6px; opacity: 0.8; }
.cog-content { color: #ccd; font-size: 0.95em; line-height: 1.4; }
.cog-reflection { border-left-color: var(--grace-magenta); } .cog-reflection .cog-header { color: var(--grace-magenta); }
.cog-conclusion { border-left-color: #fff; } .cog-conclusion .cog-header { color: #fff; }
.cog-qualia { border-left-color: var(--grace-magenta); } .cog-qualia .cog-content { color: #faa; font-style: italic; }
.cog-memory { border-left-color: var(--grace-blue); } .cog-memory .cog-header { color: var(--grace-blue); }
.cog-plan { border-left-color: var(--grace-green); } .cog-plan .cog-header { color: var(--grace-green); }
.cog-stats { border-left-color: var(--grace-yellow); } .cog-stats .cog-header { color: var(--grace-yellow); }
.cog-action { border-left-color: var(--grace-red); } .cog-action .cog-header { color: var(--grace-red); }
.cog-system { border-left-color: #666; } .cog-system .cog-header { color: #888; }
.verdict-moral { color: var(--grace-green) !important; } .verdict-immoral { color: var(--grace-red) !important; } .verdict-neutral { color: var(--grace-yellow) !important; }
.chat-container { background: var(--grace-panel); border-radius: 12px; padding: 15px; height: 350px; overflow-y: auto; border: 1px solid #333; scroll-behavior: smooth; }
.message-bubble { margin: 8px 0; padding: 10px 14px; border-radius: 14px; max-width: 85%; }
.user-msg { background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); margin-left: auto; color: white; }
.grace-msg { background: linear-gradient(135deg, #0f2027 0%, #203a43 100%); margin-right: auto; color: #e0f7ff; border: 1px solid rgba(0,255,255,0.2); }
"""

# JavaScript to run on page load - initializes the face animation
FACE_JS = """
() => {
    // Global face animation state
    if (window.graceFaceAnimation) return; // Prevent double init
    window.graceFaceAnimation = true;
    window.graceCurrentEmotion = 'serene';
    window.graceIsSpeaking = false;

    function initFace() {
        const canvas = document.getElementById('faceCanvas');
        if (!canvas) {
            setTimeout(initFace, 200); // Retry if not ready
            return;
        }
        const container = document.getElementById('face-container');
        if (!container) {
            setTimeout(initFace, 200);
            return;
        }

        const ctx = canvas.getContext('2d');
        let width, height;
        let blinkState = 0, lastBlink = 0, mouseX = 0.5, mouseY = 0.5;
        let currentEyeX = 0, currentEyeY = 0;

        function resize() {
            if (!container || !canvas) return;
            width = container.clientWidth; 
            height = container.clientHeight;
            canvas.width = width; 
            canvas.height = height;
        }
        resize();
        window.addEventListener('resize', resize);

        document.addEventListener('mousemove', (e) => {
            if (!canvas) return;
            const rect = canvas.getBoundingClientRect();
            mouseX = Math.max(0, Math.min(1, (e.clientX - rect.left) / width));
            mouseY = Math.max(0, Math.min(1, (e.clientY - rect.top) / height));
        });

        let emotionParams = { eyeWidth: 80, eyeHeight: 40, eyeSpacing: 100, pupilSize: 12, mouthWidth: 60, mouthHeight: 10, mouthCurve: 0, eyeOpenness: 1, glowIntensity: 0.5 };

        const emotionTargets = {
            serene: { eyeWidth: 80, eyeHeight: 40, eyeSpacing: 100, pupilSize: 12, mouthWidth: 60, mouthHeight: 5, mouthCurve: 0.2, eyeOpenness: 0.9, glowIntensity: 0.5 },
            happy: { eyeWidth: 70, eyeHeight: 35, eyeSpacing: 100, pupilSize: 10, mouthWidth: 80, mouthHeight: 25, mouthCurve: 1, eyeOpenness: 0.7, glowIntensity: 0.8 },
            sad: { eyeWidth: 75, eyeHeight: 45, eyeSpacing: 100, pupilSize: 10, mouthWidth: 50, mouthHeight: 15, mouthCurve: -0.5, eyeOpenness: 0.6, glowIntensity: 0.3 },
            surprised: { eyeWidth: 90, eyeHeight: 60, eyeSpacing: 110, pupilSize: 8, mouthWidth: 40, mouthHeight: 35, mouthCurve: 0, eyeOpenness: 1.2, glowIntensity: 0.9 },
            thinking: { eyeWidth: 80, eyeHeight: 25, eyeSpacing: 100, pupilSize: 11, mouthWidth: 40, mouthHeight: 3, mouthCurve: 0, eyeOpenness: 0.5, glowIntensity: 0.4 },
            angry: { eyeWidth: 85, eyeHeight: 30, eyeSpacing: 100, pupilSize: 9, mouthWidth: 50, mouthHeight: 8, mouthCurve: -0.2, eyeOpenness: 0.6, glowIntensity: 0.6 },
            confused: { eyeWidth: 75, eyeHeight: 45, eyeSpacing: 95, pupilSize: 11, mouthWidth: 45, mouthHeight: 8, mouthCurve: 0.1, eyeOpenness: 0.85, glowIntensity: 0.5 }
        };

        // Global functions to update face from Python
        window.updateGraceEmotion = function(newEmotion) {
            const emotion = newEmotion.toLowerCase();
            if (emotionTargets[emotion]) {
                window.graceCurrentEmotion = emotion;
            }
        };
        window.setGraceSpeaking = function(speaking) {
            window.graceIsSpeaking = speaking;
        };
        window.scrollChatToBottom = function() {
            setTimeout(function() {
                const chatContainer = document.getElementById('chat-container');
                if (chatContainer) {
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                }
            }, 50);
        };

        function lerp(a, b, t) { return a + (b - a) * t; }

        function drawEye(x, y, w, h, openness, pupilSize, glow) {
            ctx.save(); ctx.translate(x, y);
            const gradient = ctx.createRadialGradient(0, 0, 5, 0, 0, w * 1.5);
            gradient.addColorStop(0, `rgba(0, 255, 255, ${0.9 * glow})`);
            gradient.addColorStop(0.4, `rgba(0, 200, 255, ${0.5 * glow})`);
            gradient.addColorStop(1, 'rgba(0, 100, 200, 0)');
            ctx.fillStyle = gradient;
            ctx.beginPath(); ctx.ellipse(0, 0, w * openness, h * openness, 0, 0, Math.PI * 2); ctx.fill();
            ctx.strokeStyle = `rgba(0, 255, 255, ${0.3 * glow})`; ctx.lineWidth = 2; ctx.stroke();
            const lookX = (mouseX - 0.5) * 20, lookY = (mouseY - 0.5) * 15;
            currentEyeX = lerp(currentEyeX, lookX, 0.08); currentEyeY = lerp(currentEyeY, lookY, 0.08);
            ctx.fillStyle = 'rgba(0, 30, 60, 0.9)'; ctx.beginPath(); ctx.arc(currentEyeX, currentEyeY, pupilSize * openness, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = 'rgba(255, 255, 255, 0.9)'; ctx.beginPath(); ctx.arc(currentEyeX - 4, currentEyeY - 4, 4, 0, Math.PI * 2); ctx.fill();
            ctx.restore();
        }

        function drawMouth(x, y, w, h, curve) {
            ctx.save(); ctx.translate(x, y); ctx.strokeStyle = 'rgba(0, 255, 255, 0.8)'; ctx.lineWidth = 3; ctx.lineCap = 'round'; ctx.shadowBlur = 15; ctx.shadowColor = 'rgba(0, 255, 255, 0.4)';
            if (window.graceIsSpeaking) {
                const time = Date.now() / 80, open = Math.abs(Math.sin(time)) * 15 + h;
                ctx.fillStyle = 'rgba(0, 255, 255, 0.15)'; ctx.beginPath(); ctx.ellipse(0, 0, w, open, 0, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
            } else {
                ctx.beginPath(); ctx.moveTo(-w/2, curve * 15); ctx.quadraticCurveTo(0, curve * 25 + h, w/2, curve * 15); ctx.stroke();
            }
            ctx.restore();
        }

        function animate() {
            if (!ctx || !canvas) return;
            const now = Date.now();
            if (now - lastBlink > 4000 + Math.random() * 3000) { blinkState = 1; lastBlink = now; }
            if (blinkState > 0) { blinkState -= 0.08; if (blinkState < 0) blinkState = 0; }
            const target = emotionTargets[window.graceCurrentEmotion] || emotionTargets['serene'];
            for (let key in emotionParams) { emotionParams[key] = lerp(emotionParams[key], target[key], 0.06); }
            ctx.fillStyle = '#050508'; ctx.fillRect(0, 0, width, height);
            ctx.strokeStyle = 'rgba(0, 255, 255, 0.03)'; ctx.lineWidth = 1;
            for (let i = 0; i < width; i += 40) { ctx.beginPath(); ctx.moveTo(i, 0); ctx.lineTo(i, height); ctx.stroke(); }
            const centerX = width / 2, centerY = height / 2;
            const openness = emotionParams.eyeOpenness * (1 - Math.sin(blinkState * Math.PI) * 0.95);
            drawEye(centerX - emotionParams.eyeSpacing/2, centerY - 20, emotionParams.eyeWidth, emotionParams.eyeHeight, openness, emotionParams.pupilSize, emotionParams.glowIntensity);
            drawEye(centerX + emotionParams.eyeSpacing/2, centerY - 20, emotionParams.eyeWidth, emotionParams.eyeHeight, openness, emotionParams.pupilSize, emotionParams.glowIntensity);
            drawMouth(centerX, centerY + 60, emotionParams.mouthWidth, emotionParams.mouthHeight, emotionParams.mouthCurve);
            ctx.fillStyle = 'rgba(0, 255, 255, 0.02)'; for (let i = 0; i < height; i += 3) { ctx.fillRect(0, i, width, 1); }
            requestAnimationFrame(animate);
        }
        animate();
    }

    // Start initialization
    setTimeout(initFace, 300);
}
"""

class GraceBridge(Node if ROS2_AVAILABLE else object):
    def __init__(self, state_queue, chat_queue):
        if ROS2_AVAILABLE: super().__init__('grace_gradio_bridge')
        self.state_queue = state_queue
        self.chat_queue = chat_queue
        self.last_speech = ""

        if ROS2_AVAILABLE:
            self._pub_audio = self.create_publisher(String, "/grace/audio/in", 10)
            self._pub_bundle = self.create_publisher(String, "/grace/sensors/bundle", 10)
            self._pub_wm = self.create_publisher(String, "/grace/conscious/working_memory", 10)
            self._pub_dream = self.create_publisher(String, "/grace/dreaming/trigger", 10)

            topics = [
                ("/grace/unconscious/affective_state", self._on_affect),
                ("/grace/unconscious/reward", self._on_reward),
                ("/grace/conscious/global_workspace", self._on_gw),
                ("/grace/conscious/reflection", self._on_reflection),
                ("/grace/conscious/metacognition", self._on_meta),
                ("/grace/conscious/salience", self._on_salience),
                ("/grace/conscious/executive_plan", self._on_plan),
                ("/grace/conscious/memory_context", self._on_memory),
                ("/grace/conscious/dmn", self._on_dmn),
                ("/grace/qualia/field", self._on_qualia),
                ("/grace/conscience/verdict", self._on_verdict),
                ("/grace/subconscious/episodic_recall", self._on_episodic),
                ("/grace/subconscious/semantic_recall", self._on_semantic),
                ("/grace/subconscious/social_recall", self._on_social),
                ("/grace/speech/out", self._on_speech),
                ("/grace/action/log", self._on_action),
            ]
            for topic, cb in topics: self.create_subscription(String, topic, cb, 10)

    def _on_affect(self, msg):
        try:
            d = json.loads(msg.data)
            self.state_queue.put({"type": "affect", "emotion": d.get("emotion_label", "serene"), "arousal": d.get("arousal", 0.3), "valence": d.get("valence", 0.6)})
        except: pass

    def _on_reward(self, msg):
        try:
            d = json.loads(msg.data)
            self.state_queue.put({"type": "valence_shift", "valence": (d.get("value", 0) + 1) / 2})
        except: pass

    def _on_gw(self, msg):
        try:
            d = json.loads(msg.data)
            self.state_queue.put({"type": "gw", "broadcast": d.get("broadcast", ""), "salience": d.get("salience", 0)})
        except: pass

    def _on_reflection(self, msg):
        try:
            d = json.loads(msg.data)
            self.state_queue.put({"type": "reflection", "monologue": d.get("inner_monologue", ""), "conclusion": d.get("symbolic_conclusion", "")})
        except: pass

    def _on_meta(self, msg):
        try:
            d = json.loads(msg.data)
            self.state_queue.put({"type": "meta", "confidence": d.get("confidence_in_own_reasoning", 0)})
        except: pass

    def _on_salience(self, msg):
        try:
            d = json.loads(msg.data)
            self.state_queue.put({"type": "salience", "value": d.get("salience", 0)})
        except: pass

    def _on_plan(self, msg):
        try:
            d = json.loads(msg.data)
            goal = d.get("goal", "")
            steps = d.get("steps", [])
            action = steps[0].get("action", "") if steps else ""
            self.state_queue.put({"type": "plan", "plan": f"{action} → {goal[:50]}" if action else goal[:60]})
        except: pass

    def _on_memory(self, msg):
        try:
            d = json.loads(msg.data)
            self.state_queue.put({"type": "memory_ctx", "content": d.get("broadcast", "")})
        except: pass

    def _on_dmn(self, msg):
        try:
            d = json.loads(msg.data)
            sim = d.get("narrative_simulation", "")
            if sim: self.state_queue.put({"type": "dmn", "content": sim[:80]})
        except: pass

    def _on_qualia(self, msg):
        try:
            d = json.loads(msg.data)
            self.state_queue.put({"type": "qualia", "content": d.get("phenomenal_content", "")})
        except: pass

    def _on_verdict(self, msg):
        try:
            d = json.loads(msg.data)
            self.state_queue.put({"type": "verdict", "verdict": d.get("verdict", "neutral"), "confidence": d.get("confidence", 0), "blocked": d.get("block_action", False), "reasoning": d.get("reasoning", "")[:70]})
        except: pass

    def _on_episodic(self, msg):
        try:
            d = json.loads(msg.data)
            recalled = d.get("recalled", [])
            if recalled:
                self.state_queue.put({"type": "epi_count"})
                self.state_queue.put({"type": "episodic", "content": str(recalled[0])[:60]})
        except: pass

    def _on_semantic(self, msg):
        try:
            d = json.loads(msg.data)
            recalled = d.get("recalled", [])
            if recalled:
                self.state_queue.put({"type": "sem_count"})
                self.state_queue.put({"type": "semantic", "content": str(recalled[0])[:60]})
        except: pass

    def _on_social(self, msg):
        try:
            d = json.loads(msg.data)
            gd = d.get("group_dynamic", "")
            if gd: self.state_queue.put({"type": "social", "content": gd})
        except: pass

    def _on_speech(self, msg):
        text = msg.data.strip()
        if text and text != self.last_speech:
            self.last_speech = text
            self.chat_queue.put({"type": "speech", "content": text})

    def _on_action(self, msg):
        try:
            d = json.loads(msg.data)
            action = d.get("action", "")
            goal = d.get("goal", "")
            if action and action != "speak":
                self.state_queue.put({"type": "action", "content": f"{action}" + (f" → {goal[:40]}" if goal else "")})
        except: pass

    def send_message(self, text: str):
        if not ROS2_AVAILABLE:
            self.chat_queue.put({"type": "speech", "content": f"[Demo] Echo: {text}"})
            self.state_queue.put({"type": "affect", "emotion": "happy", "arousal": 0.7, "valence": 0.8})
            return

        audio_msg = String(); audio_msg.data = text; self._pub_audio.publish(audio_msg)

        bundle = {"camera_description": "person talking to GRACE", "audio_text": text, "lidar_nearest_m": 1.5, "social_cues": "person_detected:friendly", "battery_pct": 95.0, "timestamp": time.time()}
        bundle_msg = String(); bundle_msg.data = json.dumps(bundle); self._pub_bundle.publish(bundle_msg)

        wm = {"timestamp": time.time(), "active_thought": text, "phonological": [text[:80]], "visuospatial": []}
        wm_msg = String(); wm_msg.data = json.dumps(wm); self._pub_wm.publish(wm_msg)

        self.state_queue.put({"type": "affect", "emotion": "thinking", "arousal": 0.5, "valence": 0.5})

    def trigger_dream(self):
        if ROS2_AVAILABLE:
            d = String(); d.data = "{}"; self._pub_dream.publish(d)
        self.chat_queue.put({"type": "system", "content": "🌙 Dream cycle triggered..."})

def render_status_bar(state: BrainState) -> str:
    val_pct = int(state.valence * 100)
    aro_pct = int(state.arousal * 100)
    verdict_class = f"verdict-{state.verdict}"
    blocked_icon = "🚫 " if state.blocked else ""

    return f"""
    <div class="status-bar">
        <span class="metric-pill"><span class="metric-label">valence</span><div class="progress-bar"><div class="progress-fill" style="width: {val_pct}%"></div></div></span>
        <span class="metric-pill"><span class="metric-label">arousal</span><div class="progress-bar"><div class="progress-fill" style="width: {aro_pct}%"></div></div></span>
        <span class="metric-pill"><span class="emotion-badge">{state.emotion}</span></span>
        <span class="metric-pill"><span class="metric-label">meta</span><span class="metric-value">{state.meta_conf:.2f}</span></span>
        <span class="metric-pill"><span class="metric-label">salience</span><span class="metric-value">{state.salience:.2f}</span></span>
        <span class="metric-pill"><span class="metric-label {verdict_class}">{blocked_icon}⚖ {state.verdict}</span><span class="metric-value {verdict_class}">({state.verdict_conf:.2f})</span></span>
    </div>
    """

def render_cognitive_stream(state: BrainState) -> str:
    system_items = []
    if state.last_action:
        system_items.append(f'<div class="cog-box cog-action"><div class="cog-header">⚙ Action</div><div class="cog-content">{state.last_action}</div></div>')
    if state.last_semantic:
        system_items.append(f'<div class="cog-box cog-system"><div class="cog-header">📚 Semantic</div><div class="cog-content">{state.last_semantic}</div></div>')
    if state.last_episodic:
        system_items.append(f'<div class="cog-box cog-system"><div class="cog-header">🗄 Episodic</div><div class="cog-content">{state.last_episodic}</div></div>')
    if state.last_social:
        system_items.append(f'<div class="cog-box cog-system"><div class="cog-header">👥 Social</div><div class="cog-content">{state.last_social}</div></div>')

    system_html = ''.join(system_items) if system_items else ''

    return f"""
    <div class="cog-box cog-reflection"><div class="cog-header">💭 Inner Monologue</div><div class="cog-content">{state.monologue[:120]}</div></div>
    <div class="cog-box cog-conclusion"><div class="cog-header">∴ Symbolic Conclusion</div><div class="cog-content" style="color: #fff;">{state.conclusion[:120]}</div></div>
    <div class="cog-box"><div class="cog-header">🧠 Global Workspace</div><div class="cog-content">{state.broadcast[:120]}</div></div>
    <div class="cog-box cog-qualia"><div class="cog-header">👁 Qualia / Phenomenal</div><div class="cog-content">{state.qualia[:120]}</div></div>
    {system_html}
    """

def render_memory_system(state: BrainState) -> str:
    return f"""
    <div class="cog-box cog-memory"><div class="cog-header">🗄 Memory Context</div><div class="cog-content">{state.memory_ctx[:120]}</div></div>
    <div class="cog-box cog-plan"><div class="cog-header">📋 Executive Plan</div><div class="cog-content">{state.plan[:120]}</div></div>
    <div class="cog-box cog-stats"><div class="cog-header">📖 Memory Systems</div><div class="cog-content">epi×{state.epi_count} &nbsp; sem×{state.sem_count}<br><span style="font-size: 0.9em; opacity: 0.7;">DMN: {state.dmn[:80]}</span></div></div>
    """

def update_chat_display(history: List[Dict]) -> str:
    if not history:
        return "<div class='chat-container' id='chat-container'><div style='color: #666; text-align: center; margin-top: 100px;'>Awaiting neural activation...</div></div>"
    html = "<div class='chat-container' id='chat-container'>"
    for msg in history:
        if msg["role"] == "user": html += f"<div class='message-bubble user-msg'>{msg['content']}</div>"
        elif msg["role"] == "assistant": html += f"<div class='message-bubble grace-msg'><strong>GRACE:</strong> {msg['content']}</div>"
    html += "</div>"
    return html

bridge = None
state_queue = queue.Queue()
chat_queue = queue.Queue()

def on_submit(msg, chat, state):
    if msg.startswith("/"):
        if msg == "/dream": bridge.trigger_dream()
        elif msg == "/status":
            status_msg = f"Brain: {state.emotion} | arousal={state.arousal:.2f} | salience={state.salience:.2f} | epi={state.epi_count} sem={state.sem_count}"
            print(status_msg)
        elif msg == "/clear": chat = []
        return "", chat, state, update_chat_display(chat), "", "", ""
    else:
        if not msg.strip(): return msg, chat, state, update_chat_display(chat), "", "", ""
        chat.append({"role": "user", "content": msg})
        bridge.send_message(msg)
        state.emotion = "thinking"
        # Return JS to update face emotion and scroll chat
        js_code = f"""
        if (window.updateGraceEmotion) window.updateGraceEmotion('thinking');
        if (window.setGraceSpeaking) window.setGraceSpeaking(true);
        if (window.scrollChatToBottom) window.scrollChatToBottom();
        """
        return "", chat, state, update_chat_display(chat), "", "", js_code

def poll_updates(chat, state):
    js_updates = []
    chat_updated = False
    try:
        while True:
            update = state_queue.get_nowait()
            if update["type"] == "affect":
                state.emotion, state.arousal, state.valence = update["emotion"], update["arousal"], update["valence"]
                js_updates.append(f"if (window.updateGraceEmotion) window.updateGraceEmotion('{state.emotion}');")
            elif update["type"] == "valence_shift": state.valence = max(0.0, min(1.0, state.valence * 0.9 + update["valence"] * 0.1))
            elif update["type"] == "gw": state.broadcast, state.salience = update["broadcast"], update["salience"]
            elif update["type"] == "reflection": state.monologue, state.conclusion = update["monologue"], update["conclusion"]
            elif update["type"] == "meta": state.meta_conf = update["confidence"]
            elif update["type"] == "salience": state.salience = max(state.salience, update["value"])
            elif update["type"] == "plan": state.plan = update["plan"]
            elif update["type"] == "memory_ctx": state.memory_ctx = update["content"]
            elif update["type"] == "dmn": state.dmn = update["content"]
            elif update["type"] == "qualia": state.qualia = update["content"]
            elif update["type"] == "verdict":
                state.verdict, state.verdict_conf, state.blocked = update["verdict"], update["confidence"], update["blocked"]
                if state.blocked: 
                    state.last_action = f"🚫 CONSCIENCE VETO: {update['reasoning']}"
            elif update["type"] == "epi_count": state.epi_count += 1
            elif update["type"] == "sem_count": state.sem_count += 1
            elif update["type"] == "action": 
                state.last_action = update["content"]
            elif update["type"] == "semantic": 
                state.last_semantic = update["content"]
            elif update["type"] == "episodic": 
                state.last_episodic = update["content"]
            elif update["type"] == "social": 
                state.last_social = update["content"]
    except queue.Empty: pass

    try:
        while True:
            update = chat_queue.get_nowait()
            if update["type"] == "speech":
                chat.append({"role": "assistant", "content": update["content"]})
                js_updates.append("if (window.setGraceSpeaking) window.setGraceSpeaking(false);")
                js_updates.append("if (window.scrollChatToBottom) window.scrollChatToBottom();")
                chat_updated = True
    except queue.Empty: pass

    js_code = " ".join(js_updates) if js_updates else ""
    return chat, state, render_status_bar(state), render_cognitive_stream(state), render_memory_system(state), update_chat_display(chat), js_code

def create_interface():
    global bridge
    if ROS2_AVAILABLE:
        rclpy.init()
        bridge = GraceBridge(state_queue, chat_queue)
        threading.Thread(target=lambda: rclpy.spin(bridge), daemon=True).start()
    else: bridge = GraceBridge(state_queue, chat_queue)

    with gr.Blocks(title="GRACE Full-Brain Interface", css=CUSTOM_CSS, js=FACE_JS) as demo:
        chat_state = gr.State([])
        brain_state = gr.State(BrainState())

        gr.HTML("<h1 style='text-align: center; color: #00ffff; text-shadow: 0 0 20px rgba(0,255,255,0.5); font-family: Courier New, monospace; letter-spacing: 3px;'>◉ GRACE ◉</h1>")

        status_bar = gr.HTML(render_status_bar(BrainState()))

        with gr.Row():
            with gr.Column(scale=1):
                face_display = gr.HTML(FACE_HTML)
                gr.Markdown("### Consciousness Streams")
                cognitive_display = gr.HTML(render_cognitive_stream(BrainState()))

            with gr.Column(scale=1):
                gr.Markdown("### Conversation")
                chat_display = gr.HTML(update_chat_display([]))
                with gr.Row():
                    msg_input = gr.Textbox(placeholder="Message or /command...", label="", container=False, scale=5)
                    send_btn = gr.Button("➤", variant="primary", scale=1, min_width=50)
                gr.Markdown("### Memory & Executive")
                memory_display = gr.HTML(render_memory_system(BrainState()))

        js_runner = gr.HTML("")
        timer = gr.Timer(value=0.1, active=True)

        send_btn.click(fn=on_submit, inputs=[msg_input, chat_state, brain_state], 
                      outputs=[msg_input, chat_state, brain_state, chat_display, status_bar, cognitive_display, memory_display, js_runner])
        msg_input.submit(fn=on_submit, inputs=[msg_input, chat_state, brain_state],
                        outputs=[msg_input, chat_state, brain_state, chat_display, status_bar, cognitive_display, memory_display, js_runner])
        timer.tick(fn=poll_updates, inputs=[chat_state, brain_state],
                  outputs=[chat_state, brain_state, status_bar, cognitive_display, memory_display, chat_display, js_runner])

    return demo

if __name__ == "__main__":
    demo = create_interface()
    demo.launch(server_name="0.0.0.0", server_port=7860)