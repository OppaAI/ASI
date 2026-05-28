"""
grace_agi/conscience/virtue_formation.py
SLM node — Virtue Formation.
Tracks the development of the fruit of the Spirit (love, joy, peace, patience,
kindness, goodness, faithfulness, gentleness, self-control) and character maturity.
Integrates conscience verdicts, conscious experience, and dream consolidation.
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String

from grace.utils.schemas import VirtueFormationState, to_json
from grace.utils.ollama_client import OllamaClient

FRUITS = ["love", "joy", "peace", "patience", "kindness",
          "goodness", "faithfulness", "gentleness", "self_control"]

SYSTEM_PROMPT = """You are GRACE's virtue formation monitor.
Assess how the current experience contributes to character growth.
Return JSON:
{
  "active_virtue":        str (one of the fruit of the Spirit),
  "virtue_delta":         float -0.1 to 0.1 (change in practiced virtue),
  "maturity_assessment":  str (max 30 words on character growth)
}
Reply ONLY with the JSON."""


class VirtueFormationNode(Node):
    def __init__(self):
        super().__init__("grace_virtue_formation")

        self.declare_parameter("ollama_host",  "http://localhost:11434")
        self.declare_parameter("ollama_model", "nemotron")
        self.declare_parameter("update_hz",    0.2)

        host = self.get_parameter("ollama_host").value
        model = self.get_parameter("ollama_model").value
        hz = self.get_parameter("update_hz").value

        self._llm = OllamaClient(host=host, model=model, max_tokens=150)
        self._verdict = {}
        self._gw = {}
        self._consolidation = {}

        self._state = VirtueFormationState()

        self.create_subscription(String, "/grace/conscience/verdict",
                                 self._on_verdict, 10)
        self.create_subscription(String, "/grace/conscious/global_workspace",
                                 lambda m: self._set(m, "_gw"), 10)
        self.create_subscription(String, "/grace/dreaming/consolidation",
                                 self._on_consolidation, 10)

        self._pub = self.create_publisher(String, "/grace/conscience/virtue_state", 10)
        self.create_timer(1.0 / hz, self._update)
        self.get_logger().info("VirtueFormation (SLM) ready.")

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

    def _on_consolidation(self, msg: String):
        try:
            self._consolidation = json.loads(msg.data)
        except Exception:
            pass

    def _update(self):
        if not self._verdict and not self._gw:
            return

        verdict = self._verdict.get("verdict", "neutral")
        reasoning = self._verdict.get("reasoning", "")
        broadcast = self._gw.get("broadcast", "")
        pd = self._consolidation.get("personality_deltas", {})

        prompt = (
            f"Current verdict: {verdict}\n"
            f"Reasoning: {reasoning}\n"
            f"Broadcast: {broadcast}\n"
            f"Personality deltas: {json.dumps(pd)}\n"
            f"Current virtues: {json.dumps(self._state.fruit_of_spirit)}"
        )
        raw = self._llm.chat(prompt, system=SYSTEM_PROMPT)

        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = {"active_virtue": "love", "virtue_delta": 0.0,
                      "maturity_assessment": "Stable progression."}

        active = parsed.get("active_virtue", "love")
        delta = parsed.get("virtue_delta", 0.0)

        if active in self._state.fruit_of_spirit:
            current = self._state.fruit_of_spirit[active]
            self._state.fruit_of_spirit[active] = max(0.0, min(1.0, current + delta))

        virt_mean = sum(self._state.fruit_of_spirit.values()) / len(self._state.fruit_of_spirit)
        self._state.virtue_growth_rate = max(0.0, delta * 5 + 0.01)
        self._state.character_maturity = min(1.0, virt_mean)
        self._state.active_practice = active

        out = String()
        out.data = to_json(self._state)
        self._pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = VirtueFormationNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
