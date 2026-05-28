"""
grace_agi/hidden_workspace/introspective_access.py
Hidden Workspace — Introspective Access (SLM node)
Generates introspective self-reports from metacognition and hidden content.
"""
import json
import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from grace.utils.schemas import IntrospectiveAccessState, to_json
from grace.utils.ollama_client import OllamaClient


SYSTEM_PROMPT = """You are GRACE's introspective access engine.
Given metacognitive awareness, private reflections, and narrative coherence,
generate an introspective self-report. Return JSON:
  "self_report_generated": bool,
  "access_quality": float 0-1 (how transparent self-access is),
  "metacognitive_accuracy": float 0-1,
  "introspection_depth": float 0-1,
  "reported_content": string (the introspective report)
Reply ONLY with the JSON object."""


class IntrospectiveAccessNode(Node):
    def __init__(self):
        super().__init__("grace_introspective_access")

        self.declare_parameter("ollama_host",  "http://localhost:11434")
        self.declare_parameter("ollama_model", "nemotron")
        self.declare_parameter("update_hz", 0.2)

        host  = self.get_parameter("ollama_host").value
        model = self.get_parameter("ollama_model").value
        hz    = self.get_parameter("update_hz").value

        self._llm = OllamaClient(host=host, model=model, max_tokens=320)
        self._metacognition = ""
        self._private_reflection = ""
        self._narrative_coherence = ""

        self.create_subscription(String, "/grace/conscious/metacognition",
                                 self._on_metacognition, 10)
        self.create_subscription(String, "/grace/hidden/private_reflection",
                                 self._on_reflection, 10)
        self.create_subscription(String, "/grace/hidden/narrative_coherence",
                                 self._on_narrative, 10)

        self._pub = self.create_publisher(String, "/grace/hidden/introspective_access", 10)
        self.create_timer(1.0 / hz if hz > 0 else 5.0, self._tick)
        self.get_logger().info("Introspective Access (SLM) ready.")

    def _on_metacognition(self, msg: String):
        try:
            d = json.loads(msg.data)
            self._metacognition = (
                f"confidence={d.get('confidence_in_own_reasoning',0.5):.2f} "
                f"flags={d.get('epistemic_flags',[])} "
                f"redirect={d.get('redirect_to_executive',False)}"
            )
        except Exception:
            pass

    def _on_reflection(self, msg: String):
        try:
            d = json.loads(msg.data)
            self._private_reflection = d.get("reflection_text", "")[:200]
        except Exception:
            pass

    def _on_narrative(self, msg: String):
        try:
            d = json.loads(msg.data)
            self._narrative_coherence = (
                f"coherence={d.get('coherence_score',0.7):.2f} "
                f"gaps={d.get('gaps_detected',0)} "
                f"continuity={d.get('self_continuity',0.7):.2f}"
            )
        except Exception:
            pass

    def _tick(self):
        if not self._metacognition and not self._private_reflection and not self._narrative_coherence:
            return  # No data — skip LLM call

        prompt = (f"Metacognition: {self._metacognition}\n"
                  f"Private reflection: {self._private_reflection}\n"
                  f"Narrative coherence: {self._narrative_coherence}")
        raw = self._llm.chat(prompt, system=SYSTEM_PROMPT)
        try:
            parsed = json.loads(raw)
            state = IntrospectiveAccessState(
                timestamp=time.time(),
                self_report_generated=parsed.get("self_report_generated", False),
                access_quality=round(float(parsed.get("access_quality", 0.5)), 3),
                metacognitive_accuracy=round(float(parsed.get("metacognitive_accuracy", 0.5)), 3),
                introspection_depth=round(float(parsed.get("introspection_depth", 0.3)), 3),
                reported_content=parsed.get("reported_content", ""),
            )
        except Exception:
            state = IntrospectiveAccessState(
                timestamp=time.time(),
                self_report_generated=False,
                access_quality=0.3,
                metacognitive_accuracy=0.3,
                introspection_depth=0.2,
                reported_content="[introspection offline]",
            )

        out = String()
        out.data = to_json(state)
        self._pub.publish(out)
        self.get_logger().debug("Introspective access report published.")


def main(args=None):
    rclpy.init(args=args)
    node = IntrospectiveAccessNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
