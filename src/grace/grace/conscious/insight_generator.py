"""
grace_agi/conscious/insight_generator.py
SLM node — Insight Generator.
Generates Aha! moments and insight by restructuring mental models.
Integrates global workspace content, reflection outputs, dream distillation,
and metacognitive assessment to produce novel understanding.
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String

from grace.utils.schemas import InsightState, to_json
from grace.utils.ollama_client import OllamaClient

SYSTEM_PROMPT = """You are GRACE's insight generation system.
Detect opportunities for sudden understanding (Aha! moments) and generate
novel insight by restructuring available information.
Return JSON:
{
  "insight_occurred":          bool,
  "insight_content":           str (max 50 words),
  "restructuring_description": str (max 40 words),
  "aha_intensity":             float 0-1,
  "incubation_required":       bool,
  "insight_source":            str
}
Reply ONLY with the JSON."""


class InsightGeneratorNode(Node):
    def __init__(self):
        super().__init__("grace_insight_generator")

        self.declare_parameter("ollama_host",  "http://localhost:11434")
        self.declare_parameter("ollama_model", "nemotron")
        self.declare_parameter("update_hz",    0.2)

        host = self.get_parameter("ollama_host").value
        model = self.get_parameter("ollama_model").value
        hz = self.get_parameter("update_hz").value

        self._llm = OllamaClient(host=host, model=model, max_tokens=200)
        self._gw = {}
        self._reflection = {}
        self._distillation = {}
        self._metacog = {}

        self._state = InsightState()
        self._insight_history: list[str] = []

        self.create_subscription(String, "/grace/conscious/global_workspace",
                                 lambda m: self._set(m, "_gw"), 10)
        self.create_subscription(String, "/grace/conscious/reflection",
                                 lambda m: self._set(m, "_reflection"), 10)
        self.create_subscription(String, "/grace/dreaming/distillation",
                                 lambda m: self._set(m, "_distillation"), 10)
        self.create_subscription(String, "/grace/conscious/metacognition",
                                 lambda m: self._set(m, "_metacog"), 10)

        self._pub = self.create_publisher(String, "/grace/conscious/insight", 10)
        self.create_timer(1.0 / hz, self._update)
        self.get_logger().info("InsightGenerator (SLM) ready.")

    def _set(self, msg, attr):
        try:
            setattr(self, attr, json.loads(msg.data))
        except Exception:
            pass

    def _update(self):
        broadcast = self._gw.get("broadcast", "")
        mono = self._reflection.get("inner_monologue", "")
        symbolic = self._reflection.get("symbolic_conclusion", "")
        distilled = self._distillation.get("distilled_knowledge", "")
        compressed = self._distillation.get("compressed_patterns", [])
        confidence = self._metacog.get("confidence_in_own_reasoning", 0.5)
        ep_flags = self._metacog.get("epistemic_flags", [])

        if not broadcast:
            return

        recent = " | ".join(self._insight_history[-5:])

        prompt = (
            f"Broadcast: {broadcast}\n"
            f"Monologue: {mono}\n"
            f"Conclusion: {symbolic}\n"
            f"Distilled knowledge: {distilled}\n"
            f"Compressed patterns: {json.dumps(compressed)}\n"
            f"Metacognition: conf={confidence:.2f}, flags={ep_flags}\n"
            f"Recent insights: {recent}"
        )
        raw = self._llm.chat(prompt, system=SYSTEM_PROMPT)

        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = {
                "insight_occurred": False, "insight_content": "",
                "restructuring_description": "", "aha_intensity": 0.0,
                "incubation_required": False, "insight_source": "",
            }

        self._state.insight_occurred = parsed.get("insight_occurred", False)
        self._state.insight_content = parsed.get("insight_content", "")
        self._state.restructuring_description = parsed.get("restructuring_description", "")
        self._state.aha_intensity = max(0.0, min(1.0, parsed.get("aha_intensity", 0.0)))
        self._state.incubation_required = parsed.get("incubation_required", False)
        self._state.insight_source = parsed.get("insight_source", "")

        if self._state.insight_occurred and self._state.insight_content:
            self._insight_history.append(self._state.insight_content)
            self._insight_history = self._insight_history[-20:]

        out = String()
        out.data = to_json(self._state)
        self._pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = InsightGeneratorNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
