"""
grace_agi/dreaming/imagination.py
SLM node — Imagination & Counterfactual Simulator.
What-if engine driven by dream content and the Default Mode Network.
Generates novel scenarios, creative hypotheses, and behavioural alternatives
that feed the Distillation node.
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String

from grace.grace.utils.ollama_client import OllamaClient

SYSTEM_PROMPT = """You are GRACE's imagination and counterfactual simulator.
Given a dream narrative and recent environment context, generate creative
what-if scenarios that GRACE could learn from.
Return JSON:
{
  "counterfactuals": [
    {"scenario": str, "outcome": str, "lesson": str}
  ],
  "creative_hypotheses": [str],
  "behavioural_alternatives": [str],
  "novelty_score": float 0-1
}
Reply ONLY with the JSON. Generate 2-3 counterfactuals."""


class ImaginationNode(Node):
    def __init__(self):
        super().__init__("grace_imagination")

        self.declare_parameter("ollama_host",  "http://localhost:11434")
        self.declare_parameter("ollama_model", "nemotron")

        host  = self.get_parameter("ollama_host").value
        model = self.get_parameter("ollama_model").value

        self._llm   = OllamaClient(host=host, model=model, max_tokens=400)
        self._dream = {}
        self._dmn   = {}

        self.create_subscription(String, "/grace/dreaming/dream_content",
                                 self._on_dream, 10)
        self.create_subscription(String, "/grace/conscious/dmn",
                                 self._on_dmn, 10)

        self._pub = self.create_publisher(String, "/grace/dreaming/imagination", 10)
        self.get_logger().info("Imagination (SLM) ready.")

    def _on_dream(self, msg: String):
        try:
            self._dream = json.loads(msg.data)
            self._simulate()
        except Exception: pass

    def _on_dmn(self, msg: String):
        try: self._dmn = json.loads(msg.data)
        except Exception: pass

    def _simulate(self):
        if not self._dream:
            return

        narrative  = self._dream.get("dream_narrative", "")
        creativity = self._dmn.get("creativity_seed", "")
        tone       = self._dream.get("emotional_tone", "neutral")

        prompt = (f"Dream narrative: {narrative}\n"
                  f"Creativity seed: {creativity}\n"
                  f"Emotional tone: {tone}")

        raw = self._llm.chat(prompt, system=SYSTEM_PROMPT)
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = {
                "counterfactuals":           [],
                "creative_hypotheses":       [raw[:200]],
                "behavioural_alternatives":  [],
                "novelty_score":             0.5,
            }

        parsed["timestamp"] = time.time()
        out = String(); out.data = json.dumps(parsed)
        self._pub.publish(out)
        self.get_logger().info(
            f"Imagination: {len(parsed.get('counterfactuals',[]))} counterfactuals generated, "
            f"novelty={parsed.get('novelty_score',0):.2f}")


def main(args=None):
    rclpy.init(args=args)
    node = ImaginationNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
