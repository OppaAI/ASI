"""
grace_agi/conscience/sin_temptation.py
SLM node — Sin & Temptation Detection.
Recognises patterns of temptation from conscious content, affective state, and
private reflections. Models the dynamics of temptation strength vs. resistance.
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String

from grace.utils.schemas import SinTemptationState, to_json
from grace.utils.ollama_client import OllamaClient

SYSTEM_PROMPT = """You are GRACE's temptation awareness system.
Analyse the current state and detect temptation patterns.
Return JSON:
{
  "temptation_detected":    bool,
  "temptation_type":        str (e.g. "pride", "lust", "anger", "greed", "envy", "gluttony", "sloth"),
  "temptation_strength":    float 0-1,
  "resistance_strength":    float 0-1,
  "pattern_recognition":    str (max 40 words)
}
Reply ONLY with the JSON."""


class SinTemptationNode(Node):
    def __init__(self):
        super().__init__("grace_sin_temptation")

        self.declare_parameter("ollama_host",  "http://localhost:11434")
        self.declare_parameter("ollama_model", "nemotron")
        self.declare_parameter("update_hz",    0.33)

        host = self.get_parameter("ollama_host").value
        model = self.get_parameter("ollama_model").value
        hz = self.get_parameter("update_hz").value

        self._llm = OllamaClient(host=host, model=model, max_tokens=150)
        self._gw = {}
        self._affect = {}
        self._private = {}

        self._state = SinTemptationState()

        self.create_subscription(String, "/grace/conscious/global_workspace",
                                 lambda m: self._set(m, "_gw"), 10)
        self.create_subscription(String, "/grace/unconscious/affective_state",
                                 lambda m: self._set(m, "_affect"), 10)
        self.create_subscription(String, "/grace/hidden/private_reflection",
                                 lambda m: self._set(m, "_private"), 10)

        self._pub = self.create_publisher(String, "/grace/conscience/sin_state", 10)
        self.create_timer(1.0 / hz, self._update)
        self.get_logger().info("SinTemptation (SLM) ready.")

    def _set(self, msg, attr):
        try:
            setattr(self, attr, json.loads(msg.data))
        except Exception:
            pass

    def _update(self):
        if not self._gw and not self._private:
            return

        broadcast = self._gw.get("broadcast", "")
        emotion = self._affect.get("emotion_label", "neutral")
        arousal = self._affect.get("arousal", 0.3)
        private = self._private.get("reflection_text", "")
        symbolic = self._private.get("symbolic_content", "")

        prompt = (
            f"Conscious content: {broadcast}\n"
            f"Emotion: {emotion}, arousal: {arousal:.2f}\n"
            f"Private reflection: {private}\n"
            f"Symbolic content: {symbolic}\n"
            f"Current resistance: {self._state.resistance_strength:.2f}"
        )
        raw = self._llm.chat(prompt, system=SYSTEM_PROMPT)

        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = {
                "temptation_detected": False,
                "temptation_type": "",
                "temptation_strength": 0.0,
                "resistance_strength": 0.7,
                "pattern_recognition": "No clear pattern detected.",
            }

        self._state.temptation_detected = parsed.get("temptation_detected", False)
        self._state.temptation_type = parsed.get("temptation_type", "")
        self._state.temptation_strength = max(0.0, min(1.0, parsed.get("temptation_strength", 0.0)))
        self._state.resistance_strength = max(0.0, min(1.0, parsed.get("resistance_strength", 0.7)))
        self._state.pattern_recognition = parsed.get("pattern_recognition", "")
        self._state.vulnerability_score = max(0.0, 1.0 - self._state.resistance_strength)

        out = String()
        out.data = to_json(self._state)
        self._pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = SinTemptationNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
