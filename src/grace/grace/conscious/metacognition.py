"""
grace_agi/conscious/metacognition.py
SLM node — Metacognition Layer.
Self-awareness, metacognitive feelings, and epistemic agency.
Monitors the quality of reasoning and redirects the executive when needed.
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.utils.schemas import MetacogOutput, to_json
from grace.utils.ollama_client import OllamaClient

SYSTEM_PROMPT = """You are GRACE's metacognition layer.
Assess the quality and confidence of the current conscious reasoning.
Return JSON:
{
  "confidence_in_own_reasoning": float 0-1,
  "epistemic_flags":             [str],
  "redirect_to_executive":       bool,
  "self_awareness_note":         str (max 30 words)
}
Reply ONLY with the JSON."""


class MetacognitionNode(Node):
    def __init__(self):
        super().__init__("grace_metacognition")

        self.declare_parameter("ollama_host",  "http://localhost:11434")
        self.declare_parameter("ollama_model", "nemotron")

        host  = self.get_parameter("ollama_host").value
        model = self.get_parameter("ollama_model").value
        self._llm = OllamaClient(host=host, model=model, max_tokens=150)

        self._gw  = {}
        self._ref = {}
        self._verdict = {}

        self.create_subscription(String, "/grace/conscious/global_workspace",
                                 lambda m: self._set(m, "_gw"),      10)
        self.create_subscription(String, "/grace/conscious/reflection",
                                 lambda m: self._set(m, "_ref"),     10)
        self.create_subscription(String, "/grace/conscience/verdict",
                                 lambda m: self._set(m, "_verdict"), 10)

        self._pub = self.create_publisher(String, "/grace/conscious/metacognition", 10)
        self.create_timer(2.0, self._assess)
        self.get_logger().info("Metacognition (SLM) ready.")

    def _set(self, msg, attr):
        try: setattr(self, attr, json.loads(msg.data))
        except Exception: pass

    def _assess(self):
        broadcast  = self._gw.get("broadcast", "")
        monologue  = self._ref.get("inner_monologue", "")
        conclusion = self._ref.get("symbolic_conclusion", "")
        verdict    = self._verdict.get("verdict", "neutral")
        confidence = self._verdict.get("confidence", 1.0)

        if not broadcast:
            return

        prompt = (f"Broadcast: {broadcast}\n"
                  f"Monologue: {monologue}\n"
                  f"Conclusion: {conclusion}\n"
                  f"Moral verdict: {verdict} (conf={confidence:.2f})")

        raw = self._llm.chat(prompt, system=SYSTEM_PROMPT)
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = {
                "confidence_in_own_reasoning": 0.7,
                "epistemic_flags":             [],
                "redirect_to_executive":       False,
                "self_awareness_note":         raw[:100],
            }

        meta = MetacogOutput(
            confidence_in_own_reasoning=parsed.get("confidence_in_own_reasoning", 0.7),
            epistemic_flags=parsed.get("epistemic_flags", []),
            redirect_to_executive=parsed.get("redirect_to_executive", False),
        )
        out = String(); out.data = to_json(meta)
        self._pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = MetacognitionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
