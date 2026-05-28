"""
grace_agi/unconscious/affective_core.py
SLM node — Affective & Interoceptive Core.
Maintains Valence-Arousal-Dominance state with slow homeostatic decay
and constructs emotion labels via Nemotron.
"""
import json
import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from grace.utils.schemas import AffectiveState, to_json
from grace.utils.ollama_client import OllamaClient


SYSTEM_PROMPT = """You are GRACE's affective core.
Given the current VAD state and a triggering event, return JSON:
  "valence": float 0-1,
  "arousal": float 0-1,
  "dominance": float 0-1,
  "emotion_label": string (one word),
  "homeostatic_drives": {"curiosity": float, "safety": float, "energy": float}
Reply ONLY with the JSON object."""

BASELINE = {"valence": 0.6, "arousal": 0.3, "dominance": 0.5}
DECAY    = 0.05    # per-cycle drift back to baseline


class AffectiveCoreNode(Node):
    def __init__(self):
        super().__init__("grace_affective_core")

        self.declare_parameter("unconscious_hz", 5.0)
        self.declare_parameter("ollama_host",    "http://localhost:11434")
        self.declare_parameter("ollama_model",   "nemotron")

        hz    = self.get_parameter("unconscious_hz").value
        host  = self.get_parameter("ollama_host").value
        model = self.get_parameter("ollama_model").value

        self._llm   = OllamaClient(host=host, model=model, max_tokens=128)
        self._state = AffectiveState(**BASELINE, emotion_label="serene")
        self._last_event = ""

        self.create_subscription(String, "/grace/unconscious/affective_state",
                                 self._on_update, 10)
        self.create_subscription(String, "/grace/sensors/bundle",
                                 self._on_sensor, 10)

        self._pub = self.create_publisher(String, "/grace/unconscious/affective_state", 10)
        self.create_timer(1.0 / hz, self._tick)

        self.get_logger().info("AffectiveCore (SLM) ready.")

    def _on_update(self, msg: String):
        try:
            d = json.loads(msg.data)
            # Blend incoming update (don't overwrite — weighted merge)
            for k in ("valence", "arousal", "dominance"):
                if k in d:
                    cur = getattr(self._state, k)
                    setattr(self._state, k, round(cur * 0.6 + d[k] * 0.4, 3))
        except Exception:
            pass

    def _on_sensor(self, msg: String):
        try:
            bundle = json.loads(msg.data)
            # Proximity threat raises arousal
            lidar = bundle.get("lidar_nearest_m", 99.0)
            if lidar < 0.5:
                self._last_event = f"obstacle very close: {lidar:.2f}m"
            elif bundle.get("audio_text"):
                self._last_event = f"audio: {bundle['audio_text'][:60]}"
            elif bundle.get("social_cues"):
                self._last_event = f"social: {bundle['social_cues']}"
        except Exception:
            pass

    def _tick(self):
        # Homeostatic decay toward baseline
        for k, base in BASELINE.items():
            cur = getattr(self._state, k)
            setattr(self._state, k, round(cur + (base - cur) * DECAY, 3))

        # LLM update if there's an event
        if self._last_event:
            vad_str = (f"valence={self._state.valence:.2f}, "
                       f"arousal={self._state.arousal:.2f}, "
                       f"dominance={self._state.dominance:.2f}")
            prompt  = f"Current state: {vad_str}. Event: {self._last_event}"
            raw = self._llm.chat(prompt, system=SYSTEM_PROMPT)
            try:
                parsed = json.loads(raw)
                for k in ("valence", "arousal", "dominance"):
                    if k in parsed:
                        setattr(self._state, k, round(float(parsed[k]), 3))
                self._state.emotion_label       = parsed.get("emotion_label", "neutral")
                self._state.homeostatic_drives  = parsed.get("homeostatic_drives", {})
            except Exception:
                pass
            self._last_event = ""

        self._state.timestamp = time.time()
        out = String()
        out.data = to_json(self._state)
        self._pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = AffectiveCoreNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
