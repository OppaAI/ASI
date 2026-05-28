"""
grace_agi/conscience/moral_reasoning.py
SLM node — Moral Reasoning Engine.
Applies scripture principles to a concrete situation using Nemotron
and emits a structured moral analysis consumed by the Conscience Core.
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String

from grace.utils.ollama_client import OllamaClient

SYSTEM_PROMPT = """You are GRACE's moral reasoning engine.
You are given a situation description and a list of ethical principles
derived from scripture. Your job is to identify which principles apply
and how they bear on the situation.

Return ONLY a JSON object:
{
  "applicable_principles": [
    {"id": str, "relevance": float 0-1, "applies_how": str}
  ],
  "overall_moral_risk":   float 0-1,
  "recommended_verdict":  "moral" | "immoral" | "neutral" | "uncertain",
  "reasoning_summary":    str (max 80 words),
  "primary_verse":        str
}"""


class MoralReasoningNode(Node):
    def __init__(self):
        super().__init__("grace_moral_reasoning")

        self.declare_parameter("ollama_host",  "http://localhost:11434")
        self.declare_parameter("ollama_model", "nemotron")
        self.declare_parameter("strictness",   0.8)

        host       = self.get_parameter("ollama_host").value
        model      = self.get_parameter("ollama_model").value
        self._strictness = self.get_parameter("strictness").value

        self._llm        = OllamaClient(host=host, model=model, max_tokens=400)
        self._principles = []
        self._pending_situations: list[str] = []

        self.create_subscription(String, "/grace/conscience/knowledge",
                                 self._on_knowledge, 10)
        # Situations to evaluate come from the Conscience Core subscriber chain
        self.create_subscription(String, "/grace/conscience/situation",
                                 self._on_situation, 10)

        self._pub = self.create_publisher(String, "/grace/conscience/reasoning", 10)
        self.get_logger().info("MoralReasoning (SLM) ready.")

    def _on_knowledge(self, msg: String):
        try:
            d = json.loads(msg.data)
            self._principles = d.get("principles", [])
        except Exception: pass

    def _on_situation(self, msg: String):
        try:
            d = json.loads(msg.data)
            situation = d.get("situation", "")
            if situation:
                self._pending_situations.append(situation)
                self._evaluate(situation)
        except Exception: pass

    def _evaluate(self, situation: str):
        if not self._principles:
            self.get_logger().warn("MoralReasoning: no principles loaded yet.")
            return

        # Filter to likely-relevant principles via keyword match first
        # (saves tokens before the LLM call)
        words = situation.lower().split()
        relevant = [
            p for p in self._principles
            if any(kw in situation.lower() for kw in p.get("keywords", []))
        ] or self._principles[:5]   # fallback: first 5

        prompt = (f"Situation: {situation}\n"
                  f"Applicable principles: {json.dumps(relevant)}\n"
                  f"Moral strictness level: {self._strictness}")

        raw = self._llm.chat(prompt, system=SYSTEM_PROMPT)

        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = {
                "applicable_principles": [],
                "overall_moral_risk":    0.0,
                "recommended_verdict":   "uncertain",
                "reasoning_summary":     raw[:200],
                "primary_verse":         "",
            }

        parsed["situation"]  = situation
        parsed["timestamp"]  = time.time()

        out = String()
        out.data = json.dumps(parsed)
        self._pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = MoralReasoningNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
