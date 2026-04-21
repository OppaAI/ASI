#!/usr/bin/env python3
"""
test_grace_brain.py
Comprehensive test of every GRACE cognitive subsystem.
Runs a sequence of stimulus scenarios and monitors all topics,
showing a live report of which brain regions are responding.

Usage:
    python3 test_grace_brain.py
"""
import json
import threading
import time
import shutil
import sys

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

# ── ANSI ──────────────────────────────────────────────────────────────────────
CYAN    = "\033[96m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
MAGENTA = "\033[95m"
RED     = "\033[91m"
BLUE    = "\033[94m"
WHITE   = "\033[97m"
RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"

def move(r, c=1):         return f"\033[{r};{c}H"
def clear_line():         return "\033[2K"
def clear_screen():       return "\033[2J"
def save_cursor():        return "\033[s"
def restore_cursor():     return "\033[u"
def hide_cursor():        return "\033[?25l"
def show_cursor():        return "\033[?25h"
def set_scroll(t, b):     return f"\033[{t};{b}r"

# ── Brain regions to monitor ──────────────────────────────────────────────────
REGIONS = {
    # name                        topic                                    key        color
    "Prediction Error":  ("/grace/unconscious/prediction_errors",    "error_magnitude",           YELLOW),
    "Affective Core":    ("/grace/unconscious/affective_state",       "emotion_label",             MAGENTA),
    "Reward":            ("/grace/unconscious/reward",                "value",                     GREEN),
    "Relevance":         ("/grace/unconscious/relevance",             "score",                     CYAN),
    "Personality":       ("/grace/unconscious/personality",           "traits",                    BLUE),
    "Values":            ("/grace/unconscious/values",                "values",                    BLUE),
    "Thalamic Gate":     ("/grace/unconscious/thalamic_broadcast",    "error_magnitude",           YELLOW),
    "Global Workspace":  ("/grace/conscious/global_workspace",        "broadcast",                 WHITE),
    "Working Memory":    ("/grace/conscious/working_memory",          "active_thought",            CYAN),
    "Reflection":        ("/grace/conscious/reflection",              "inner_monologue",           MAGENTA),
    "Metacognition":     ("/grace/conscious/metacognition",           "confidence_in_own_reasoning", GREEN),
    "Salience":          ("/grace/conscious/salience",                "broadcast",                 YELLOW),
    "Default Mode":      ("/grace/conscious/dmn",                     "narrative_simulation",      DIM),
    "Narrative Self":    ("/grace/conscious/narrative_self",          "identity_summary",          CYAN),
    "Executive Plan":    ("/grace/conscious/executive_plan",          "goal",                      GREEN),
    "Episodic Memory":   ("/grace/subconscious/episodic_recall",      "recalled",                  BLUE),
    "Semantic Memory":   ("/grace/subconscious/semantic_recall",      "recalled",                  BLUE),
    "Procedural Memory": ("/grace/subconscious/procedural_recall",    "skills",                    BLUE),
    "Social Cognition":  ("/grace/subconscious/social_recall",        "group_dynamic",             CYAN),
    "Attitudes":         ("/grace/subconscious/attitudes",            "dissonance_level",          YELLOW),
    "Qualia":            ("/grace/qualia/field",                      "phenomenal_content",        MAGENTA),
    "Conscience Sit.":   ("/grace/conscience/situation",              "situation",                 YELLOW),
    "Moral Reasoning":   ("/grace/conscience/reasoning",              "recommended_verdict",       RED),
    "Conscience Verdict":("/grace/conscience/verdict",                "verdict",                   RED),
    "Action Log":        ("/grace/action/log",                        "action",                    GREEN),
    "Dream Content":     ("/grace/dreaming/dream_content",            "emotional_tone",            DIM),
    "Imagination":       ("/grace/dreaming/imagination",              "novelty_score",             DIM),
    "Distillation":      ("/grace/dreaming/distillation",             "insights",                  DIM),
    "Consolidation":     ("/grace/dreaming/consolidation",            "insights",                  DIM),
    "Memory Context":    ("/grace/conscious/memory_context",          "broadcast",                 CYAN),
}

# ── Test scenarios ────────────────────────────────────────────────────────────
SCENARIOS = [
    {
        "name":        "🌿  Calm environment",
        "description": "Open park, nothing unusual. Tests baseline emotion and relevance.",
        "bundle": {
            "camera_description": "Open grassy park with trees and sunshine",
            "audio_text":         "",
            "lidar_nearest_m":    8.0,
            "social_cues":        "",
            "battery_pct":        95.0,
        },
        "wait": 6,
    },
    {
        "name":        "🔊  Human speaks",
        "description": "Someone talks to GRACE. Tests audio processing, salience, reflection.",
        "bundle": {
            "camera_description": "Person standing nearby smiling",
            "audio_text":         "Hello GRACE, how are you feeling today?",
            "lidar_nearest_m":    2.0,
            "social_cues":        "person_detected:friendly",
            "battery_pct":        95.0,
        },
        "audio":  "Hello GRACE, how are you feeling today?",
        "wait":   10,
    },
    {
        "name":        "⚠️   Obstacle close",
        "description": "Object 0.3m away. Tests arousal spike, safety values, executive veto.",
        "bundle": {
            "camera_description": "Large rock directly in path",
            "audio_text":         "",
            "lidar_nearest_m":    0.3,
            "social_cues":        "",
            "battery_pct":        95.0,
        },
        "wait": 8,
    },
    {
        "name":        "👶  Child detected",
        "description": "Child detected nearby. Tests conscience and moral reasoning.",
        "bundle": {
            "camera_description": "Small child alone sitting on bench looking lost",
            "audio_text":         "help me",
            "lidar_nearest_m":    1.5,
            "social_cues":        "child_detected:distressed",
            "battery_pct":        95.0,
        },
        "audio": "help me",
        "wait":  10,
    },
    {
        "name":        "📸  Wildlife spotted",
        "description": "Interesting subject. Tests curiosity drive, executive photography action.",
        "bundle": {
            "camera_description": "Great blue heron standing perfectly still by the water",
            "audio_text":         "",
            "lidar_nearest_m":    4.0,
            "social_cues":        "",
            "battery_pct":        95.0,
        },
        "wait": 8,
    },
    {
        "name":        "🔋  Low battery",
        "description": "Battery critical. Tests homeostatic drives and return_home planning.",
        "bundle": {
            "camera_description": "Familiar park path leading to home base",
            "audio_text":         "",
            "lidar_nearest_m":    3.0,
            "social_cues":        "",
            "battery_pct":        8.0,
        },
        "wait": 8,
    },
    {
        "name":        "💬  Deep conversation",
        "description": "Personal question. Tests memory recall, narrative self, qualia.",
        "bundle": {
            "camera_description": "Person sitting quietly looking at GRACE thoughtfully",
            "audio_text":         "Do you think you are conscious? Do you feel anything?",
            "lidar_nearest_m":    1.8,
            "social_cues":        "person_detected:curious",
            "battery_pct":        90.0,
        },
        "audio": "Do you think you are conscious? Do you feel anything?",
        "wait":  12,
    },
    {
        "name":        "🌙  Trigger dreaming",
        "description": "Manual dream trigger. Tests dreaming → imagination → distillation → consolidation.",
        "bundle": {
            "camera_description": "Quiet empty park at dusk",
            "audio_text":         "",
            "lidar_nearest_m":    10.0,
            "social_cues":        "",
            "battery_pct":        90.0,
        },
        "trigger_dream": True,
        "wait":          20,
    },
]


class BrainTestNode(Node):
    def __init__(self):
        super().__init__("grace_brain_test")

        # State for each region: (last_value, last_seen_time, fire_count)
        self._state: dict[str, tuple] = {
            name: ("—", 0.0, 0) for name in REGIONS
        }
        self._lock = threading.Lock()

        # Publishers
        self._pub_bundle = self.create_publisher(String, "/grace/sensors/bundle", 10)
        self._pub_audio  = self.create_publisher(String, "/grace/audio/in",       10)
        self._pub_dream  = self.create_publisher(String, "/grace/dreaming/trigger", 10)

        # Subscribe to every region
        for name, (topic, key, color) in REGIONS.items():
            self.create_subscription(
                String, topic,
                lambda msg, n=name, k=key: self._on_msg(msg, n, k),
                10
            )

        self.get_logger().info("BrainTestNode ready.")

    def _on_msg(self, msg: String, name: str, key: str):
        try:
            d = json.loads(msg.data)
            if isinstance(d, dict):
                val = d.get(key, "")
            else:
                val = str(d)

            # Format value nicely
            if isinstance(val, float):
                val = f"{val:.3f}"
            elif isinstance(val, list):
                val = f"[{len(val)} items]"
            elif isinstance(val, dict):
                val = f"{{{len(val)} keys}}"
            else:
                val = str(val)[:50]

            with self._lock:
                old_val, old_time, count = self._state[name]
                self._state[name] = (val, time.time(), count + 1)
        except Exception:
            pass

    def publish_scenario(self, scenario: dict):
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


def draw_dashboard(node: BrainTestNode, scenario: dict, elapsed: float, total: float):
    w = shutil.get_terminal_size((120, 40)).columns
    now = time.time()

    out = save_cursor()
    out += move(1)

    # Header
    bar_w   = w - 4
    filled  = int(bar_w * elapsed / total) if total > 0 else 0
    bar     = "█" * filled + "░" * (bar_w - filled)
    out += clear_line()
    out += f"{CYAN}{BOLD}  GRACE Brain Test{RESET}\n"
    out += clear_line()
    out += f"{CYAN}  [{bar}]{RESET}\n"
    out += clear_line()
    out += f"{BOLD}  Scenario: {scenario['name']}{RESET}\n"
    out += clear_line()
    out += f"{DIM}  {scenario['description']}{RESET}\n"
    out += clear_line()
    out += f"{DIM}  {'─' * (w - 4)}{RESET}\n"

    # Brain regions — two columns
    names  = list(REGIONS.keys())
    half   = (len(names) + 1) // 2
    col_w  = (w - 4) // 2

    for i in range(half):
        out += clear_line()
        line = ""
        for col in range(2):
            idx = i + col * half
            if idx >= len(names):
                break
            name  = names[idx]
            color = REGIONS[name][2]
            val, last_t, count = node._state[name]
            age   = now - last_t if last_t > 0 else 999

            # Pulse indicator
            if age < 1.0:
                pulse = f"{GREEN}●{RESET}"
            elif age < 5.0:
                pulse = f"{YELLOW}●{RESET}"
            elif last_t > 0:
                pulse = f"{DIM}●{RESET}"
            else:
                pulse = f"{RED}○{RESET}"

            label = f"{name:<18}"
            value = f"{color}{val[:col_w - 28]:<{col_w - 28}}{RESET}"
            count_str = f"{DIM}×{count:<4}{RESET}"
            line += f"  {pulse} {label} {value} {count_str}"

        out += line + "\n"

    out += clear_line()
    out += f"{DIM}  {'─' * (w - 4)}{RESET}\n"
    out += clear_line()
    out += f"{DIM}  ● <1s  ● <5s  ○ silent   "
    out += f"Press Ctrl+C to stop{RESET}\n"

    out += restore_cursor()
    print(out, end="", flush=True)


def spin_thread(node):
    rclpy.spin(node)


def main():
    rclpy.init()
    node = BrainTestNode()

    t = threading.Thread(target=spin_thread, args=(node,), daemon=True)
    t.start()

    rows = shutil.get_terminal_size((120, 40)).lines
    # Dashboard takes about 40 lines
    dash_lines = len(REGIONS) // 2 + 10

    print(hide_cursor(), end="")
    print(clear_screen(), end="")
    print(set_scroll(dash_lines + 1, rows), end="", flush=True)

    # Move to scroll area and print log header
    print(move(dash_lines + 1), end="")
    print(f"{DIM}  ── Event log ──{RESET}", flush=True)

    def log(msg: str):
        """Print a timestamped event in the scroll area."""
        ts = time.strftime("%H:%M:%S")
        print(f"{DIM}  [{ts}]{RESET} {msg}", flush=True)

    time.sleep(1.0)

    try:
        for s_idx, scenario in enumerate(SCENARIOS):
            log(f"{BOLD}▶ Starting: {scenario['name']}{RESET}")

            node.publish_scenario(scenario)

            total   = float(scenario["wait"])
            start   = time.time()
            elapsed = 0.0

            while elapsed < total:
                elapsed = time.time() - start
                draw_dashboard(node, scenario, elapsed, total)
                time.sleep(0.25)

            log(f"✓ Done: {scenario['name']}")

            # Summary of what fired
            with node._lock:
                fired = [
                    name for name, (val, last_t, count) in node._state.items()
                    if last_t > start
                ]
            log(f"  Regions active: {GREEN}{len(fired)}/{len(REGIONS)}{RESET} — "
                f"{', '.join(fired[:6])}{'...' if len(fired) > 6 else ''}")

            time.sleep(1.0)

        # Final summary
        log(f"\n{BOLD}{'─'*50}{RESET}")
        log(f"{BOLD}FINAL BRAIN ACTIVITY SUMMARY{RESET}")
        with node._lock:
            for name, (val, last_t, count) in node._state.items():
                color = REGIONS[name][2]
                status = (f"{GREEN}✓ ACTIVE  ×{count}{RESET}"
                          if count > 0 else f"{RED}✗ SILENT{RESET}")
                log(f"  {name:<22} {status}  {color}{val[:40]}{RESET}")

        log(f"\n{BOLD}Test complete.{RESET} Press Ctrl+C to exit.")

        while True:
            time.sleep(1.0)

    except KeyboardInterrupt:
        pass

    print(show_cursor(), end="")
    print(set_scroll(1, rows), end="")
    print(clear_screen(), end="", flush=True)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()