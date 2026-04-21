"""
grace_agi/dreaming/distillation.py
Distillation + Insight + Model Updating.
Extracts generalizable insights and model updates from imagination output.
Produces a ConsolidationPacket consumed by the Consolidation node.
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String

from grace.grace.utils.schemas import ConsolidationPacket, to_json
from grace.grace.utils.ollama_client import OllamaClient

SYSTEM_PROMPT = """You are GRACE's distillation engine — the insight extractor.
Given imagination output (counterfactuals, hypotheses, alternatives),
extract generalizable lessons that should update GRACE's models.
Return JSON:
{
  "insights":            [str],
  "personality_deltas":  {"trait_name": float_delta},
  "value_updates":       {"value_name": float_new_weight},
  "new_episodic":        [{"content": str, "emotional_tag": float, "tags": [str]}],
  "new_semantic":        [{"content": str, "confidence": float, "tags": [str]}]
}
Keep personality/value deltas small (max ±0.05). Reply ONLY with the JSON."""


class DistillationNode(Node):
    def __init__(self):
        super().__init__("grace_distillation")

        self.declare_parameter("ollama_host",  "http://localhost:11434")
        self.declare_parameter("ollama_model", "nemotron")

        host  = self.get_parameter("ollama_host").value
        model = self.get_parameter("ollama_model").value

        self._llm = OllamaClient(host=host, model=model, max_tokens=500)

        self.create_subscription(String, "/grace/dreaming/imagination",
                                 self._on_imagination, 10)

        self._pub = self.create_publisher(String, "/grace/dreaming/distillation", 10)
        self.get_logger().info("Distillation ready.")

    def _on_imagination(self, msg: String):
        try:
            imag = json.loads(msg.data)
        except Exception:
            return

        counterfactuals  = imag.get("counterfactuals", [])
        hypotheses       = imag.get("creative_hypotheses", [])
        alternatives     = imag.get("behavioural_alternatives", [])

        if not (counterfactuals or hypotheses):
            return

        prompt = (f"Counterfactuals: {json.dumps(counterfactuals)}\n"
                  f"Creative hypotheses: {hypotheses}\n"
                  f"Behavioural alternatives: {alternatives}")

        raw = self._llm.chat(prompt, system=SYSTEM_PROMPT)
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = {
                "insights":           [raw[:200]],
                "personality_deltas": {},
                "value_updates":      {},
                "new_episodic":       [],
                "new_semantic":       [],
            }

        # Clamp personality/value deltas to safe range
        for k in parsed.get("personality_deltas", {}):
            parsed["personality_deltas"][k] = max(-0.05,
                min(0.05, parsed["personality_deltas"][k]))
        for k in parsed.get("value_updates", {}):
            parsed["value_updates"][k] = max(0.0,
                min(1.0, parsed["value_updates"][k]))

        parsed["timestamp"] = time.time()
        out = String(); out.data = json.dumps(parsed)
        self._pub.publish(out)
        self.get_logger().info(
            f"Distillation: {len(parsed.get('insights',[]))} insights extracted.")


def main(args=None):
    rclpy.init(args=args)
    node = DistillationNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
