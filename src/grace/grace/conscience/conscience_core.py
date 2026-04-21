"""
grace_agi/conscience/conscience_core.py
SLM node — Conscience Core.
Receives situations from the Global Workspace, executive proposals, and
reflection; queries MoralReasoning; emits a MoralVerdict that can
veto the Central Executive.
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String

from grace.grace.utils.schemas import MoralVerdict, to_json
from grace.grace.utils.ollama_client import OllamaClient

SYSTEM_PROMPT = """You are GRACE's conscience — the final moral arbiter.
Given a moral reasoning analysis, produce a definitive verdict as JSON:
{
  "verdict":        "moral" | "immoral" | "neutral" | "uncertain",
  "reasoning":      str (max 60 words),
  "verse_reference": str,
  "confidence":     float 0-1,
  "block_action":   bool   (true only if verdict is "immoral" AND confidence > 0.7)
}
Reply ONLY with the JSON object."""


class ConscienceCoreNode(Node):
    def __init__(self):
        super().__init__("grace_conscience_core")

        self.declare_parameter("ollama_host",  "http://localhost:11434")
        self.declare_parameter("ollama_model", "nemotron")
        self.declare_parameter("strictness",   0.8)

        host       = self.get_parameter("ollama_host").value
        model      = self.get_parameter("ollama_model").value
        self._strictness = self.get_parameter("strictness").value

        self._llm = OllamaClient(host=host, model=model, max_tokens=256)

        # Receive situations from multiple upstream sources
        self.create_subscription(String, "/grace/conscious/global_workspace",
                                 self._on_gw, 10)
        self.create_subscription(String, "/grace/conscious/executive_plan",
                                 self._on_plan, 10)
        self.create_subscription(String, "/grace/conscious/reflection",
                                 self._on_reflection, 10)
        self.create_subscription(String, "/grace/conscience/reasoning",
                                 self._on_reasoning, 10)

        # Publish verdict to multiple consumers
        self._pub_verdict = self.create_publisher(String, "/grace/conscience/verdict",    10)
        self._pub_sit     = self.create_publisher(String, "/grace/conscience/situation",  10)

        self.get_logger().info("ConscienceCore (SLM) ready.")

    # ── Situation intake ──────────────────────────────────────────────────────

    def _on_gw(self, msg: String):
        try:
            gw = json.loads(msg.data)
            broadcast = gw.get("broadcast", "")
            if broadcast and gw.get("salience", 0) > 0.5:
                self._submit_situation(broadcast, source="global_workspace")
        except Exception: pass

    def _on_plan(self, msg: String):
        try:
            plan = json.loads(msg.data)
            goal = plan.get("goal", "")
            if goal:
                self._submit_situation(
                    f"Proposed action: {goal}. Steps: {plan.get('steps', [])}",
                    source="executive_plan"
                )
        except Exception: pass

    def _on_reflection(self, msg: String):
        try:
            ref = json.loads(msg.data)
            mono = ref.get("inner_monologue", "")
            if mono:
                self._submit_situation(mono, source="reflection")
        except Exception: pass

    def _on_reasoning(self, msg: String):
        """Receive moral analysis from MoralReasoning and produce final verdict."""
        try:
            analysis = json.loads(msg.data)
        except Exception:
            return

        situation = analysis.get("situation", "")
        prompt = f"Moral analysis: {json.dumps(analysis)}\nStrictness: {self._strictness}"
        raw = self._llm.chat(prompt, system=SYSTEM_PROMPT)

        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = {
                "verdict":         "uncertain",
                "reasoning":       raw[:200],
                "verse_reference": "",
                "confidence":      0.5,
                "block_action":    False,
            }

        verdict = MoralVerdict(
            situation=situation,
            verdict=parsed.get("verdict", "uncertain"),
            reasoning=parsed.get("reasoning", ""),
            verse_reference=parsed.get("verse_reference", ""),
            confidence=parsed.get("confidence", 0.5),
            block_action=parsed.get("block_action", False),
        )

        if verdict.block_action:
            self.get_logger().warn(
                f"CONSCIENCE VETO: '{situation[:60]}' — {verdict.reasoning}")

        out = String(); out.data = to_json(verdict)
        self._pub_verdict.publish(out)

    def _submit_situation(self, situation: str, source: str = ""):
        out = String()
        out.data = json.dumps({"situation": situation, "source": source,
                               "timestamp": time.time()})
        self._pub_sit.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = ConscienceCoreNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
