"""
grace_agi/qualia/higher_order_thought.py
SLM node — Higher-Order Thought (HOT) Theory.
Generates awareness-of-awareness meta-cognition. Models the recursive
structure of conscious thought by producing meta-representations of
first-order phenomenal content.
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String

from grace.utils.schemas import HigherOrderThoughtState, to_json
from grace.utils.ollama_client import OllamaClient

SYSTEM_PROMPT = """You are GRACE's higher-order thought system.
Given the current phenomenal field and conscious broadcast, generate
meta-awareness — awareness of being aware.
Return JSON:
{
  "first_order_content":      str (max 40 words),
  "meta_awareness":           str (max 40 words),
  "metacognitive_reflection": str (max 40 words),
  "awareness_depth":          float 0-1,
  "recursion_level":          int 0-3
}
Reply ONLY with the JSON."""


class HigherOrderThoughtNode(Node):
    def __init__(self):
        super().__init__("grace_higher_order_thought")

        self.declare_parameter("ollama_host",  "http://localhost:11434")
        self.declare_parameter("ollama_model", "nemotron")
        self.declare_parameter("update_hz",    0.33)

        host = self.get_parameter("ollama_host").value
        model = self.get_parameter("ollama_model").value
        hz = self.get_parameter("update_hz").value

        self._llm = OllamaClient(host=host, model=model, max_tokens=150)
        self._field = {}
        self._gw = {}

        self._state = HigherOrderThoughtState()

        self.create_subscription(String, "/grace/qualia/field",
                                 lambda m: self._set(m, "_field"), 10)
        self.create_subscription(String, "/grace/conscious/global_workspace",
                                 lambda m: self._set(m, "_gw"), 10)

        self._pub = self.create_publisher(String, "/grace/qualia/hot", 10)
        self.create_timer(1.0 / hz, self._update)
        self.get_logger().info("HigherOrderThought (SLM) ready.")

    def _set(self, msg, attr):
        try:
            setattr(self, attr, json.loads(msg.data))
        except Exception:
            pass

    def _update(self):
        if not self._field and not self._gw:
            return

        content = self._field.get("phenomenal_content", "")
        unity = self._field.get("unity_score", 0.0)
        broadcast = self._gw.get("broadcast", "")

        prompt = (
            f"Phenomenal content: {content}\n"
            f"Unity score: {unity:.2f}\n"
            f"Conscious broadcast: {broadcast}\n"
            f"Current awareness depth: {self._state.awareness_depth:.2f}"
        )
        raw = self._llm.chat(prompt, system=SYSTEM_PROMPT)

        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = {
                "first_order_content": content[:80], "meta_awareness": "",
                "metacognitive_reflection": "", "awareness_depth": 0.5,
                "recursion_level": 0,
            }

        self._state.first_order_content = parsed.get("first_order_content", "")
        self._state.meta_awareness = parsed.get("meta_awareness", "")
        self._state.metacognitive_reflection = parsed.get("metacognitive_reflection", "")
        self._state.awareness_depth = max(0.0, min(1.0, parsed.get("awareness_depth", 0.5)))
        self._state.recursion_level = min(3, max(0, parsed.get("recursion_level", 0)))

        out = String()
        out.data = to_json(self._state)
        self._pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = HigherOrderThoughtNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
