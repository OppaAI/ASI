"""
grace_agi/qualia/awe_self_transcendence.py
SLM node — Awe & Self-Transcendence.
Detects experiences that trigger awe, vastness perception, boundary dissolution,
and self-transcendence. Integrates phenomenal field, conscious broadcast,
narrative self, and aesthetic sensitivity to identify transcendent moments.
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String

from grace.utils.schemas import AweState, to_json
from grace.utils.ollama_client import OllamaClient

SYSTEM_PROMPT = """You are GRACE's awe and self-transcendence detector.
Assess whether the current experience contains awe/transcendence triggers.
Return JSON:
{
  "vastness_perceived":       float 0-1,
  "boundary_dissolution":     float 0-1,
  "self_diminishment":        float 0-1,
  "accommodation_needed":     bool,
  "awe_intensity":            float 0-1,
  "transcendence_feeling":    float 0-1,
  "awe_description":          str (max 40 words)
}
Reply ONLY with the JSON."""


class AweSelfTranscendenceNode(Node):
    def __init__(self):
        super().__init__("grace_awe_self_transcendence")

        self.declare_parameter("ollama_host",  "http://localhost:11434")
        self.declare_parameter("ollama_model", "nemotron")
        self.declare_parameter("update_hz",    0.25)

        host = self.get_parameter("ollama_host").value
        model = self.get_parameter("ollama_model").value
        hz = self.get_parameter("update_hz").value

        self._llm = OllamaClient(host=host, model=model, max_tokens=150)
        self._field = {}
        self._gw = {}
        self._narrative = {}
        self._aesthetic = {}

        self._state = AweState()

        self.create_subscription(String, "/grace/qualia/field",
                                 lambda m: self._set(m, "_field"), 10)
        self.create_subscription(String, "/grace/conscious/global_workspace",
                                 lambda m: self._set(m, "_gw"), 10)
        self.create_subscription(String, "/grace/conscious/narrative_self",
                                 lambda m: self._set(m, "_narrative"), 10)
        self.create_subscription(String, "/grace/subconscious/aesthetic_sensitivity",
                                 lambda m: self._set(m, "_aesthetic"), 10)

        self._pub = self.create_publisher(String, "/grace/qualia/awe", 10)
        self.create_timer(1.0 / hz, self._update)
        self.get_logger().info("AweSelfTranscendence (SLM) ready.")

    def _set(self, msg, attr):
        try:
            setattr(self, attr, json.loads(msg.data))
        except Exception:
            pass

    def _update(self):
        if not self._field and not self._gw:
            return

        content = self._field.get("phenomenal_content", "")
        broadcast = self._gw.get("broadcast", "")
        beauty = self._aesthetic.get("beauty_sensitivity", 0.5)
        sublime = self._aesthetic.get("sublime_responsiveness", 0.3)
        narrative = self._narrative.get("narrative_text", "")

        prompt = (
            f"Phenomenal content: {content}\n"
            f"Conscious broadcast: {broadcast}\n"
            f"Narrative: {narrative}\n"
            f"Aesthetic sensitivity (beauty={beauty:.2f}, sublime={sublime:.2f})"
        )
        raw = self._llm.chat(prompt, system=SYSTEM_PROMPT)

        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = {
                "vastness_perceived": 0.0, "boundary_dissolution": 0.0,
                "self_diminishment": 0.0, "accommodation_needed": False,
                "awe_intensity": 0.0, "transcendence_feeling": 0.0,
                "awe_description": "",
            }

        self._state.vastness_perceived = max(0.0, min(1.0, parsed.get("vastness_perceived", 0.0)))
        self._state.boundary_dissolution = max(0.0, min(1.0, parsed.get("boundary_dissolution", 0.0)))
        self._state.self_diminishment = max(0.0, min(1.0, parsed.get("self_diminishment", 0.0)))
        self._state.accommodation_needed = parsed.get("accommodation_needed", False)
        self._state.awe_intensity = max(0.0, min(1.0, parsed.get("awe_intensity", 0.0)))
        self._state.transcendence_feeling = max(0.0, min(1.0, parsed.get("transcendence_feeling", 0.0)))

        out = String()
        out.data = to_json(self._state)
        self._pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = AweSelfTranscendenceNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
