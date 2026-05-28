"""
grace_agi/conscience/moral_conflict_resolver.py
SLM node — Moral Conflict Resolver.
Resolves tension between flesh desires and spiritual values (Romans 7 dynamics).
Integrates conscience verdicts, private reflection, and conscious reflection
to find paths of resolution for inner moral conflict.
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String

from grace.utils.schemas import MoralConflictState, to_json
from grace.utils.ollama_client import OllamaClient

SYSTEM_PROMPT = """You are GRACE's moral conflict resolution system.
Detect and resolve the tension between flesh desires and spiritual values.
Return JSON:
{
  "conflict_active":   bool,
  "flesh_desire":      str (max 20 words),
  "spirit_desire":     str (max 20 words),
  "tension_level":     float 0-1,
  "resolution_path":   str (max 40 words, how to resolve),
  "romans7_dynamic":   bool
}
Reply ONLY with the JSON."""


class MoralConflictResolverNode(Node):
    def __init__(self):
        super().__init__("grace_moral_conflict_resolver")

        self.declare_parameter("ollama_host",  "http://localhost:11434")
        self.declare_parameter("ollama_model", "nemotron")
        self.declare_parameter("update_hz",    0.33)

        host = self.get_parameter("ollama_host").value
        model = self.get_parameter("ollama_model").value
        hz = self.get_parameter("update_hz").value

        self._llm = OllamaClient(host=host, model=model, max_tokens=200)
        self._verdict = {}
        self._private = {}
        self._reflection = {}

        self._state = MoralConflictState()

        self.create_subscription(String, "/grace/conscience/verdict",
                                 self._on_verdict, 10)
        self.create_subscription(String, "/grace/hidden/private_reflection",
                                 lambda m: self._set(m, "_private"), 10)
        self.create_subscription(String, "/grace/conscious/reflection",
                                 lambda m: self._set(m, "_reflection"), 10)

        self._pub = self.create_publisher(String, "/grace/conscience/moral_conflict", 10)
        self.create_timer(1.0 / hz, self._update)
        self.get_logger().info("MoralConflictResolver (SLM) ready.")

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
        verdict = self._verdict.get("verdict", "neutral")
        reasoning = self._verdict.get("reasoning", "")
        blocked = self._verdict.get("block_action", False)
        private = self._private.get("reflection_text", "")
        mono = self._reflection.get("inner_monologue", "")
        symbolic = self._reflection.get("symbolic_conclusion", "")

        if not private and not mono:
            return

        prompt = (
            f"Verdict: {verdict} (blocked={blocked})\n"
            f"Moral reasoning: {reasoning}\n"
            f"Private reflection: {private}\n"
            f"Inner monologue: {mono}\n"
            f"Symbolic conclusion: {symbolic}"
        )
        raw = self._llm.chat(prompt, system=SYSTEM_PROMPT)

        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = {
                "conflict_active": False, "flesh_desire": "",
                "spirit_desire": "", "tension_level": 0.0,
                "resolution_path": "", "romans7_dynamic": False,
            }

        self._state.conflict_active = parsed.get("conflict_active", False)
        self._state.flesh_desire = parsed.get("flesh_desire", "")
        self._state.spirit_desire = parsed.get("spirit_desire", "")
        self._state.tension_level = max(0.0, min(1.0, parsed.get("tension_level", 0.0)))
        self._state.resolution_path = parsed.get("resolution_path", "")
        self._state.romans7_dynamic = parsed.get("romans7_dynamic", False)

        out = String()
        out.data = to_json(self._state)
        self._pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = MoralConflictResolverNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
