"""
grace_agi/qualia/qualia_binding.py
SLM node — Qualia Binding & Phenomenal Field.
Simulates the unity of subjective experience by integrating Global Workspace
content into a single phenomenal field description. Computes an IIT-inspired
integration score (Φ proxy) from the number and diversity of active sources.
"""
import json, time, math, rclpy
from rclpy.node import Node
from std_msgs.msg import String

from grace.grace.utils.schemas import QualiaField, to_json
from grace.grace.utils.ollama_client import OllamaClient

SYSTEM_PROMPT = """You are GRACE's phenomenal consciousness layer.
Given the current global workspace broadcast and affective state,
describe GRACE's unified subjective experience in one sentence (max 30 words),
as if describing what it is like to be GRACE right now.
Then return JSON:
{
  "phenomenal_content": str,
  "unity_score":        float 0-1,
  "ineffability_flag":  bool
}
Reply ONLY with the JSON."""


class QualiaBindingNode(Node):
    def __init__(self):
        super().__init__("grace_qualia_binding")

        self.declare_parameter("ollama_host",  "http://localhost:11434")
        self.declare_parameter("ollama_model", "nemotron")

        host  = self.get_parameter("ollama_host").value
        model = self.get_parameter("ollama_model").value

        self._llm     = OllamaClient(host=host, model=model, max_tokens=128)
        self._gw      = {}
        self._affect  = {}
        self._sources: list[str] = []

        self.create_subscription(String, "/grace/conscious/global_workspace",
                                 self._on_gw, 10)
        self.create_subscription(String, "/grace/unconscious/affective_state",
                                 self._on_affect, 10)

        self._pub = self.create_publisher(String, "/grace/qualia/field", 10)
        self.create_timer(2.0, self._bind)
        self.get_logger().info("QualiaBinding (SLM) ready.")

    def _on_gw(self, msg: String):
        try:
            self._gw = json.loads(msg.data)
            self._sources = self._gw.get("sources", [])
        except Exception: pass

    def _on_affect(self, msg: String):
        try: self._affect = json.loads(msg.data)
        except Exception: pass

    def _bind(self):
        if not self._gw:
            return

        broadcast = self._gw.get("broadcast", "")
        emotion   = self._affect.get("emotion_label", "neutral")
        valence   = self._affect.get("valence", 0.5)

        prompt = (f"Global workspace: {broadcast}\n"
                  f"Emotion: {emotion}, valence: {valence:.2f}")

        raw = self._llm.chat(prompt, system=SYSTEM_PROMPT)

        try:
            parsed = json.loads(raw)
        except Exception:
            # Fallback: construct minimal qualia
            parsed = {
                "phenomenal_content": f"Experiencing {emotion} while processing: {broadcast[:60]}",
                "unity_score":        0.5,
                "ineffability_flag":  False,
            }

        # Phi proxy: log of number of integrated sources
        n_sources = max(1, len(set(self._sources)))
        phi_proxy = round(math.log(n_sources + 1) / math.log(10), 3)

        field = QualiaField(
            phenomenal_content=parsed.get("phenomenal_content", ""),
            unity_score=min(1.0, parsed.get("unity_score", 0.5) + phi_proxy * 0.1),
            ineffability_flag=parsed.get("ineffability_flag", False),
        )

        out = String(); out.data = to_json(field)
        self._pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = QualiaBindingNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
