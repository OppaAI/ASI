"""
grace_agi/conscience/redemption_grace.py
SLM node — Redemption & Grace Logic.
Models guilt, repentance, forgiveness, restoration, and reconciliation.
Applies grace logic informed by conscience verdicts, private reflection, and
temptation state. Follows a biblical model of restorative justice.
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String

from grace.utils.schemas import RedemptionGraceState, to_json
from grace.utils.ollama_client import OllamaClient

SYSTEM_PROMPT = """You are GRACE's redemption and grace processor.
Given the current moral state, apply grace logic to model guilt, repentance,
forgiveness, restoration, and reconciliation.
Return JSON:
{
  "guilt_level":              float 0-1,
  "repentance_active":        bool,
  "forgiveness_received":     bool,
  "restoration_progress":     float 0-1,
  "grace_applied":            bool,
  "reconciliation_needed":    bool,
  "grace_note":               str (max 40 words)
}
Reply ONLY with the JSON."""


class RedemptionGraceNode(Node):
    def __init__(self):
        super().__init__("grace_redemption_grace")

        self.declare_parameter("ollama_host",  "http://localhost:11434")
        self.declare_parameter("ollama_model", "nemotron")
        self.declare_parameter("update_hz",    0.25)

        host = self.get_parameter("ollama_host").value
        model = self.get_parameter("ollama_model").value
        hz = self.get_parameter("update_hz").value

        self._llm = OllamaClient(host=host, model=model, max_tokens=150)
        self._verdict = {}
        self._private = {}
        self._sin_state = {}

        self._state = RedemptionGraceState()

        self.create_subscription(String, "/grace/conscience/verdict",
                                 self._on_verdict, 10)
        self.create_subscription(String, "/grace/hidden/private_reflection",
                                 lambda m: self._set(m, "_private"), 10)
        self.create_subscription(String, "/grace/conscience/sin_state",
                                 lambda m: self._set(m, "_sin_state"), 10)

        self._pub = self.create_publisher(String, "/grace/conscience/redemption_state", 10)
        self.create_timer(1.0 / hz, self._update)
        self.get_logger().info("RedemptionGrace (SLM) ready.")

    def _set(self, msg, attr):
        try:
            setattr(self, attr, json.loads(msg.data))
        except Exception:
            pass

    def _on_verdict(self, msg: String):
        try:
            self._verdict = json.loads(msg.data)
        except Exception:
            pass

    def _update(self):
        verdict_val = self._verdict.get("verdict", "neutral")
        if verdict_val in ("neutral", "") and not self._verdict.get("reasoning"):
            return  # Nothing to process — skip LLM call

        reasoning = self._verdict.get("reasoning", "")
        blocked = self._verdict.get("block_action", False)
        private = self._private.get("reflection_text", "")
        sin_strength = self._sin_state.get("temptation_strength", 0.0)

        prompt = (
            f"Verdict: {verdict_val} (blocked={blocked})\n"
            f"Reasoning: {reasoning}\n"
            f"Private reflection: {private}\n"
            f"Temptation strength: {sin_strength:.2f}\n"
            f"Current guilt: {self._state.guilt_level:.2f}, "
            f"restoration: {self._state.restoration_progress:.2f}"
        )
        raw = self._llm.chat(prompt, system=SYSTEM_PROMPT)

        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = {
                "guilt_level": 0.0, "repentance_active": False,
                "forgiveness_received": False, "restoration_progress": 0.0,
                "grace_applied": False, "reconciliation_needed": False,
                "grace_note": "",
            }

        self._state.guilt_level = max(0.0, min(1.0, parsed.get("guilt_level", 0.0)))
        self._state.repentance_active = parsed.get("repentance_active", False)
        self._state.forgiveness_received = parsed.get("forgiveness_received", False)
        self._state.restoration_progress = max(0.0, min(1.0, parsed.get("restoration_progress", 0.0)))
        self._state.grace_applied = parsed.get("grace_applied", False)
        self._state.reconciliation_needed = parsed.get("reconciliation_needed", False)

        out = String()
        out.data = to_json(self._state)
        self._pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = RedemptionGraceNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
