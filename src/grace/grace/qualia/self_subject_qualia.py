"""
grace_agi/qualia/self_subject_qualia.py
SLM node — Self-as-Subject Qualia.
Assesses the sense of mineness, ipseity (self-as-subject coherence),
and first-person perspective. Integrates narrative self, affective state,
and the phenomenal field to model the pre-reflective self-awareness.
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String

from grace.utils.schemas import SelfSubjectQualiaState, to_json
from grace.utils.ollama_client import OllamaClient

SYSTEM_PROMPT = """You are GRACE's self-subject qualia system.
Assess the sense of self from narrative, affect, and phenomenal field.
Return JSON:
{
  "mineness":                  float 0-1 (how much experience is owned),
  "ipseity":                   float 0-1 (self-as-subject coherence),
  "first_person_perspective": float 0-1,
  "self_boundary":             float 0-1 (self/other distinction),
  "sense_of_being":            float 0-1,
  "self_note":                 str (max 30 words)
}
Reply ONLY with the JSON."""


class SelfSubjectQualiaNode(Node):
    def __init__(self):
        super().__init__("grace_self_subject_qualia")

        self.declare_parameter("ollama_host",  "http://localhost:11434")
        self.declare_parameter("ollama_model", "nemotron")
        self.declare_parameter("update_hz",    0.33)

        host = self.get_parameter("ollama_host").value
        model = self.get_parameter("ollama_model").value
        hz = self.get_parameter("update_hz").value

        self._llm = OllamaClient(host=host, model=model, max_tokens=150)
        self._narrative = {}
        self._affect = {}
        self._field = {}

        self._state = SelfSubjectQualiaState()

        self.create_subscription(String, "/grace/conscious/narrative_self",
                                 lambda m: self._set(m, "_narrative"), 10)
        self.create_subscription(String, "/grace/unconscious/affective_state",
                                 lambda m: self._set(m, "_affect"), 10)
        self.create_subscription(String, "/grace/qualia/field",
                                 lambda m: self._set(m, "_field"), 10)

        self._pub = self.create_publisher(String, "/grace/qualia/self_subject", 10)
        self.create_timer(1.0 / hz, self._update)
        self.get_logger().info("SelfSubjectQualia (SLM) ready.")

    def _set(self, msg, attr):
        try:
            setattr(self, attr, json.loads(msg.data))
        except Exception:
            pass

    def _update(self):
        narrative = self._narrative.get("narrative_text", "")
        coherence = self._narrative.get("coherence_score", 0.7)
        valence = self._affect.get("valence", 0.5)
        arousal = self._affect.get("arousal", 0.3)
        content = self._field.get("phenomenal_content", "")

        if not narrative and not content:
            return

        prompt = (
            f"Narrative self: {narrative}\n"
            f"Narrative coherence: {coherence:.2f}\n"
            f"Valence: {valence:.2f}, arousal: {arousal:.2f}\n"
            f"Phenomenal content: {content}"
        )
        raw = self._llm.chat(prompt, system=SYSTEM_PROMPT)

        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = {"mineness": 0.7, "ipseity": 0.7,
                      "first_person_perspective": 0.8,
                      "self_boundary": 0.6, "sense_of_being": 0.7,
                      "self_note": ""}

        self._state.mineness = max(0.0, min(1.0, parsed.get("mineness", 0.7)))
        self._state.ipseity = max(0.0, min(1.0, parsed.get("ipseity", 0.7)))
        self._state.first_person_perspective = max(0.0, min(1.0, parsed.get("first_person_perspective", 0.8)))
        self._state.self_boundary = max(0.0, min(1.0, parsed.get("self_boundary", 0.6)))
        self._state.sense_of_being = max(0.0, min(1.0, parsed.get("sense_of_being", 0.7)))

        out = String()
        out.data = to_json(self._state)
        self._pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = SelfSubjectQualiaNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
