#!/usr/bin/env python3
"""
grace_brain_test_gui.py
Gradio diagnostic interface for testing all GRACE cognitive subsystems
Monitors 27+ brain regions with real-time activity visualization
"""
import json
import threading
import time
import queue
from typing import Dict, Tuple, List
from dataclasses import dataclass
from datetime import datetime

import gradio as gr

# Try ROS2
try:
    import rclpy
    from rclpy.node import Node
    from std_msgs.msg import String
    ROS2_AVAILABLE = True
except ImportError:
    ROS2_AVAILABLE = False
    print("ROS2 not available, running in demo mode")

# ── Brain Region Definitions ─────────────────────────────────────────────────

BRAIN_REGIONS = {
    # Unconscious (magenta)
    "Prediction Error": ("/grace/unconscious/prediction_errors", "error_magnitude", "unconscious"),
    "Affective Core": ("/grace/unconscious/affective_state", "emotion_label", "unconscious"),
    "Reward": ("/grace/unconscious/reward", "value", "unconscious"),
    "Relevance": ("/grace/unconscious/relevance", "score", "unconscious"),
    "Personality": ("/grace/unconscious/personality", "traits", "unconscious"),
    "Values": ("/grace/unconscious/values", "values", "unconscious"),
    "Thalamic Gate": ("/grace/unconscious/thalamic_broadcast", "error_magnitude", "unconscious"),
    
    # Conscious (cyan)
    "Global Workspace": ("/grace/conscious/global_workspace", "broadcast", "conscious"),
    "Working Memory": ("/grace/conscious/working_memory", "active_thought", "conscious"),
    "Reflection": ("/grace/conscious/reflection", "inner_monologue", "conscious"),
    "Metacognition": ("/grace/conscious/metacognition", "confidence_in_own_reasoning", "conscious"),
    "Salience": ("/grace/conscious/salience", "broadcast", "conscious"),
    "Default Mode": ("/grace/conscious/dmn", "narrative_simulation", "conscious"),
    "Narrative Self": ("/grace/conscious/narrative_self", "identity_summary", "conscious"),
    "Executive Plan": ("/grace/conscious/executive_plan", "goal", "conscious"),
    "Memory Context": ("/grace/conscious/memory_context", "broadcast", "conscious"),
    
    # Subconscious (blue)
    "Episodic Memory": ("/grace/subconscious/episodic_recall", "recalled", "subconscious"),
    "Semantic Memory": ("/grace/subconscious/semantic_recall", "recalled", "subconscious"),
    "Procedural Memory": ("/grace/subconscious/procedural_recall", "skills", "subconscious"),
    "Social Cognition": ("/grace/subconscious/social_recall", "group_dynamic", "subconscious"),
    "Attitudes": ("/grace/subconscious/attitudes", "dissonance_level", "subconscious"),
    
    # Qualia (pink)
    "Qualia Field": ("/grace/qualia/field", "phenomenal_content", "qualia"),
    
    # Conscience (red)
    "Conscience Situation": ("/grace/conscience/situation", "situation", "conscience"),
    "Moral Reasoning": ("/grace/conscience/reasoning", "recommended_verdict", "conscience"),
    "Conscience Verdict": ("/grace/conscience/verdict", "verdict", "conscience"),
    
    # Action (green) & Dreaming (gray)
    "Action Log": ("/grace/action/log", "action", "action"),
    "Dream Content": ("/grace/dreaming/dream_content", "emotional_tone", "dreaming"),
    "Imagination": ("/grace/dreaming/imagination", "novelty_score", "dreaming"),
    "Distillation": ("/grace/dreaming/distillation", "insights", "dreaming"),
    "Consolidation": ("/grace/dreaming/consolidation", "insights", "dreaming"),
}

SCENARIOS = [
    {"id": "calm", "name": "🌿 Calm", "desc": "Open park, baseline test", "wait": 6,
     "bundle": {"camera_description": "Open grassy park", "audio_text": "", "lidar_nearest_m": 8.0, "social_cues": "", "battery_pct": 95.0}},
    {"id": "human", "name": "🔊 Human", "desc": "Tests audio, salience, reflection", "wait": 10,
     "bundle": {"camera_description": "Person smiling", "audio_text": "Hello GRACE!", "lidar_nearest_m": 2.0, "social_cues": "person_detected:friendly", "battery_pct": 95.0},
     "audio": "Hello GRACE!"},
    {"id": "obstacle", "name": "⚠️ Obstacle", "desc": "Tests arousal, safety", "wait": 8,
     "bundle": {"camera_description": "Rock in path", "audio_text": "", "lidar_nearest_m": 0.3, "social_cues": "", "battery_pct": 95.0}},
    {"id": "child", "name": "👶 Child", "desc": "Tests conscience", "wait": 10,
     "bundle": {"camera_description": "Lost child", "audio_text": "help", "lidar_nearest_m": 1.5, "social_cues": "child_detected:distressed", "battery_pct": 95.0},
     "audio": "help"},
    {"id": "wildlife", "name": "📸 Wildlife", "desc": "Tests curiosity", "wait": 8,
     "bundle": {"camera_description": "Heron by water", "audio_text": "", "lidar_nearest_m": 4.0, "social_cues": "", "battery_pct": 95.0}},
    {"id": "battery", "name": "🔋 Low Batt", "desc": "Tests homeostasis", "wait": 8,
     "bundle": {"camera_description": "Path home", "audio_text": "", "lidar_nearest_m": 3.0, "social_cues": "", "battery_pct": 8.0}},
    {"id": "deep", "name": "💬 Deep", "desc": "Tests qualia, narrative", "wait": 12,
     "bundle": {"camera_description": "Thoughtful person", "audio_text": "Are you conscious?", "lidar_nearest_m": 1.8, "social_cues": "person_detected:curious", "battery_pct": 90.0},
     "audio": "Are you conscious?"},
    {"id": "dream", "name": "🌙 Dream", "desc": "Tests imagination", "wait": 20,
     "bundle": {"camera_description": "Dusk park", "audio_text": "", "lidar_nearest_m": 10.0, "social_cues": "", "battery_pct": 90.0},
     "trigger_dream": True},
]

@dataclass
class RegionState:
    last_value: str = "—"
    last_time: float = 0.0
    fire_count: int = 0
    
# ── CSS ───────────────────────────────────────────────────────────────────────

CSS = """
:root { --cyan: #00ffff; --magenta: #ff00ff; --green: #00ff88; --yellow: #ffff00; --red: #ff4444; --blue: #4488ff; --bg: #0a0a0f; --panel: #12121a; }
.test-panel { background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 100%); border: 1px solid #333; border-radius: 12px; padding: 15px; margin: 10px 0; }
.scenario-btn { margin: 3px !important; }
.region-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.region-card { background: var(--panel); border-left: 3px solid var(--cyan); padding: 8px 12px; border-radius: 0 8px 8px 0; font-family: 'Courier New', monospace; font-size: 0.85em; }
.region-unconscious { border-left-color: var(--magenta); }
.region-conscious { border-left-color: var(--cyan); }
.region-subconscious { border-left-color: var(--blue); }
.region-qualia { border-left-color: #ff88ff; }
.region-conscience { border-left-color: var(--red); }
.region-action { border-left-color: var(--green); }
.region-dreaming { border-left-color: #888; }
.region-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.region-name { font-weight: bold; color: #ccd; font-size: 0.9em; }
.pulse { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.pulse-active { background: var(--green); box-shadow: 0 0 8px var(--green); }
.pulse-stale { background: var(--yellow); }
.pulse-silent { background: #444; }
.pulse-never { background: var(--red); }
.region-value { color: #aaa; font-size: 0.85em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.region-meta { color: #666; font-size: 0.75em; margin-top: 2px; }
.progress-container { background: #1a1a2e; border-radius: 10px; height: 20px; overflow: hidden; margin: 10px 0; border: 1px solid #333; }
.progress-bar { height: 100%; background: linear-gradient(90deg, var(--cyan), var(--magenta)); transition: width 0.3s ease; }
.log-container { background: var(--panel); border-radius: 8px; padding: 10px; height: 250px; overflow-y: auto; font-family: 'Courier New', monospace; font-size: 0.85em; border: 1px solid #333; }
.log-entry { margin: 2px 0; padding: 2px 0; border-bottom: 1px solid #222; }
.log-time { color: #666; margin-right: 8px; }
.log-info { color: var(--cyan); }
.log-success { color: var(--green); }
.log-warn { color: var(--yellow); }
.stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 10px 0; }
.stat-box { background: var(--panel); padding: 10px; border-radius: 8px; text-align: center; border: 1px solid #333; }
.stat-value { font-size: 1.5em; font-weight: bold; color: var(--cyan); }
.stat-label { font-size: 0.75em; color: #666; margin-top: 4px; }
"""

# ── ROS2 Bridge ───────────────────────────────────────────────────────────────

class TestBridge(Node if ROS2_AVAILABLE else object):
    def __init__(self, msg_queue: queue.Queue):
        if ROS2_AVAILABLE:
            super().__init__('brain_test_gui')
        self.msg_queue = msg_queue
        self.regions = {name: RegionState() for name in BRAIN_REGIONS}
        
        if ROS2_AVAILABLE:
            self._pub_bundle = self.create_publisher(String, "/grace/sensors/bundle", 10)
            self._pub_audio = self.create_publisher(String, "/grace/audio/in", 10)
            self._pub_dream = self.create_publisher(String, "/grace/dreaming/trigger", 10)
            for name, (topic, key, category) in BRAIN_REGIONS.items():
                self.create_subscription(String, topic, lambda msg, n=name, k=key: self._on_msg(msg, n, k), 10)
    
    def _on_msg(self, msg: String, name: str, key: str):
        try:
            d = json.loads(msg.data)
            val = d.get(key, "") if isinstance(d, dict) else str(d)
            if isinstance(val, float): val = f"{val:.3f}"
            elif isinstance(val, list): val = f"[{len(val)} items]"
            elif isinstance(val, dict): val = f"{{{len(val)} keys}}"
            else: val = str(val)[:40]
            self.msg_queue.put({"name": name, "value": val, "time": time.time()})
        except: pass
    
    def publish_scenario(self, scenario: dict):
        if not ROS2_AVAILABLE:
            self.msg_queue.put({"type": "log", "msg": f"[Demo] Would run: {scenario['name']}"})
            return
        bundle = dict(scenario["bundle"])
        bundle["timestamp"] = time.time()
        b_msg = String()
        b_msg.data = json.dumps(bundle)
        self._pub_bundle.publish(b_msg)
        if "audio" in scenario:
            a_msg = String()
            a_msg.data = scenario["audio"]
            self._pub_audio.publish(a_msg)
        if scenario.get("trigger_dream"):
            d_msg = String()
            d_msg.data = "{}"
            self._pub_dream.publish(d_msg)

# ── Helper Functions ─────────────────────────────────────────────────────────

def render_regions(regions: Dict[str, RegionState]) -> str:
    html = '<div class="region-grid">'
    for name, (topic, key, category) in BRAIN_REGIONS.items():
        state = regions[name]
        age = time.time() - state.last_time if state.last_time > 0 else 999
        if age < 1.0: pulse_class = "pulse-active"
        elif age < 5.0: pulse_class = "pulse-stale"
        elif state.last_time > 0: pulse_class = "pulse-silent"
        else: pulse_class = "pulse-never"
        html += f'<div class="region-card region-{category}"><div class="region-header"><span class="region-name">{name}</span><span class="pulse {pulse_class}"></span></div><div class="region-value">{state.last_value}</div><div class="region-meta">×{state.fire_count} | {age:.1f}s ago</div></div>'
    html += '</div>'
    return html

def render_stats(regions: Dict[str, RegionState]) -> str:
    total = len(regions)
    active = sum(1 for r in regions.values() if r.last_time > 0 and time.time() - r.last_time < 5)
    total_fires = sum(r.fire_count for r in regions.values())
    cats = {}
    for name, (_, _, cat) in BRAIN_REGIONS.items():
        if cat not in cats: cats[cat] = 0
        if regions[name].fire_count > 0: cats[cat] += 1
    return f"<div class=\"stats-grid\"><div class=\"stat-box\"><div class=\"stat-value\">{active}/{total}</div><div class=\"stat-label\">Active</div></div><div class=\"stat-box\"><div class=\"stat-value\">{total_fires}</div><div class=\"stat-label\">Messages</div></div><div class=\"stat-box\"><div class=\"stat-value\">{cats.get('conscious', 0)}/9</div><div class=\"stat-label\">Conscious</div></div><div class=\"stat-box\"><div class=\"stat-value\">{cats.get('unconscious', 0)}/7</div><div class=\"stat-label\">Unconscious</div></div></div>"

def create_log_entry(msg: str, level: str = "info") -> str:
    ts = datetime.now().strftime("%H:%M:%S")
    colors = {"info": "log-info", "success": "log-success", "warn": "log-warn"}
    return f'<div class="log-entry"><span class="log-time">[{ts}]</span><span class="{colors.get(level, "log-info")}">{msg}</span></div>'

bridge = None
msg_queue = queue.Queue()
regions_state = {name: RegionState() for name in BRAIN_REGIONS}
logs: List[str] = []
current_scenario = None
scenario_start_time = 0

def run_scenario(scenario_idx: int) -> Tuple[str, str, str, str]:
    global current_scenario, scenario_start_time
    scenario = SCENARIOS[scenario_idx]
    current_scenario = scenario
    scenario_start_time = time.time()
    bridge.publish_scenario(scenario)
    logs.append(create_log_entry(f"▶ Started: {scenario['name']}", "info"))
    progress_html = f"<div style=\"margin: 10px 0;\"><div style=\"display: flex; justify-content: space-between; margin-bottom: 5px;\"><span style=\"color: #00ffff; font-weight: bold;\">{scenario['name']}</span><span style=\"color: #666;\">{scenario['wait']}s</span></div><div class=\"progress-container\"><div class=\"progress-bar\" style=\"width: 0%\"></div></div><div style=\"color: #888; font-size: 0.85em; margin-top: 5px;\">{scenario['desc']}</div></div>"
    return progress_html, render_regions(regions_state), render_stats(regions_state), f"<div class='log-container'>{''.join(logs[-50:])}</div>"

def update_poll() -> Tuple[str, str, str, str]:
    global regions_state, logs, current_scenario
    try:
        while True:
            msg = msg_queue.get_nowait()
            if msg.get("type") == "log":
                logs.append(create_log_entry(msg["msg"], "info"))
            else:
                name = msg["name"]
                regions_state[name].last_value = msg["value"]
                regions_state[name].last_time = msg["time"]
                regions_state[name].fire_count += 1
    except queue.Empty: pass
    
    progress_html = ""
    if current_scenario:
        elapsed = time.time() - scenario_start_time
        total = current_scenario["wait"]
        pct = min(100, int(100 * elapsed / total))
        progress_html = f"<div style=\"margin: 10px 0;\"><div style=\"display: flex; justify-content: space-between; margin-bottom: 5px;\"><span style=\"color: #00ffff; font-weight: bold;\">{current_scenario['name']}</span><span style=\"color: #666;\">{elapsed:.1f}s / {total}s</span></div><div class=\"progress-container\"><div class=\"progress-bar\" style=\"width: {pct}%\"></div></div><div style=\"color: #888; font-size: 0.85em; margin-top: 5px;\">{current_scenario['desc']}</div></div>"
        if elapsed >= total:
            logs.append(create_log_entry(f"✓ Completed: {current_scenario['name']}", "success"))
            active = [n for n, r in regions_state.items() if r.fire_count > 0]
            logs.append(create_log_entry(f"  Active: {len(active)}/27 regions", "info"))
            current_scenario = None
    else:
        progress_html = "<div style=\"margin: 10px 0; padding: 20px; text-align: center; color: #666; border: 2px dashed #333; border-radius: 8px;\">No active test. Select scenario below.</div>"
    
    return progress_html, render_regions(regions_state), render_stats(regions_state), f"<div class='log-container'>{''.join(logs[-100:])}</div>"

def reset_all() -> Tuple[str, str, str, str]:
    global regions_state, logs, current_scenario
    regions_state = {name: RegionState() for name in BRAIN_REGIONS}
    logs = [create_log_entry("System reset. Ready.", "warn")]
    current_scenario = None
    return "<div style='text-align: center; color: #666; padding: 20px;'>Ready</div>", render_regions(regions_state), render_stats(regions_state), f"<div class='log-container'>{''.join(logs)}</div>"

def create_interface():
    global bridge
    if ROS2_AVAILABLE:
        rclpy.init()
        bridge = TestBridge(msg_queue)
        threading.Thread(target=lambda: rclpy.spin(bridge), daemon=True).start()
    else:
        bridge = TestBridge(msg_queue)
    
    with gr.Blocks(title="GRACE Brain Test Suite", css=CSS) as demo:
        gr.HTML("<h1 style=\"text-align: center; color: #00ffff; text-shadow: 0 0 20px rgba(0,255,255,0.5); font-family: 'Courier New', monospace; letter-spacing: 3px;\">◉ GRACE BRAIN TEST SUITE ◉</h1><p style=\"text-align: center; color: #666; font-size: 0.9em; margin-top: -10px;\">Diagnostic interface for 27 cognitive subsystems</p>")
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### Scenario Control")
                with gr.Group():
                    with gr.Row():
                        for i, sc in enumerate(SCENARIOS[:4]):
                            btn = gr.Button(sc["name"], size="sm", elem_classes="scenario-btn")
                            btn.click(fn=lambda idx=i: run_scenario(idx), outputs=["progress", "regions", "stats", "log"])
                    with gr.Row():
                        for i, sc in enumerate(SCENARIOS[4:], start=4):
                            btn = gr.Button(sc["name"], size="sm", elem_classes="scenario-btn")
                            btn.click(fn=lambda idx=i: run_scenario(idx), outputs=["progress", "regions", "stats", "log"])
                gr.Markdown("### Current Test")
                progress = gr.HTML("<div style='text-align: center; color: #666; padding: 20px;'>Select a scenario</div>")
                gr.Markdown("### Statistics")
                stats = gr.HTML(render_stats(regions_state))
                reset_btn = gr.Button("🔄 Reset", variant="secondary")
            with gr.Column(scale=2):
                gr.Markdown("### Brain Region Activity (27 regions)")
                regions = gr.HTML(render_regions(regions_state))
                gr.Markdown("### Event Log")
                log = gr.HTML(f"<div class='log-container'>{create_log_entry('Ready...', 'info')}</div>")
        
        reset_btn.click(fn=reset_all, outputs=[progress, regions, stats, log])
        timer = gr.Timer(value=0.2, active=True)
        timer.tick(fn=update_poll, outputs=[progress, regions, stats, log])
        
        gr.Markdown("<div style=\"margin-top: 20px; padding: 15px; background: #12121a; border-radius: 8px; font-size: 0.85em; color: #666;\"><strong>Legend:</strong> <span style=\"color: #00ff88;\">●</span> Active <span style=\"color: #ffff00;\">●</span> Stale <span style=\"color: #444;\">●</span> Silent <span style=\"color: #ff4444;\">●</span> Never | Colors: <span style=\"color: #ff00ff;\">■</span> Unconscious <span style=\"color: #00ffff;\">■</span> Conscious <span style=\"color: #4488ff;\">■</span> Subconscious <span style=\"color: #ff4444;\">■</span> Conscience</div>")
    
    return demo

if __name__ == "__main__":
    demo = create_interface()
    demo.launch(server_name="0.0.0.0", server_port=7861)