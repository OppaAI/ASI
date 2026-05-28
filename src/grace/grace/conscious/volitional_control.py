"""
grace_agi/conscious/volitional_control.py
SLM node — Volitional Control.
Models the sense of agency and intention formation. Integrates executive plans,
central executive directives, and reflection to determine whether intentions
are formed, how long deliberation takes, and whether veto power is exercised.
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String

from grace.utils.schemas import VolitionState, to_json
from grace.utils.ollama_client import OllamaClient

SYSTEM_PROMPT = """You are GRACE's volitional control system.
Model the formation of intentions and the sense of agency.
Return JSON:
{
  "intention_formed":       bool,
  "intention_content":      str (max 30 words),
  "agency_sense":           float 0-1,
  "deliberation_duration":  float (seconds),
  "decision_confidence":    float 0-1,
  "veto_power_active":      bool,
  "veto_reason":            str (max 30 words, if vetoed)
}
Reply ONLY with the JSON."""


class VolitionalControlNode(Node):
    def __init__(self):
        super().__init__("grace_volitional_control")

        self.declare_parameter("ollama_host",  "http://localhost:11434")
        self.declare_parameter("ollama_model", "nemotron")
        self.declare_parameter("update_hz",    0.5)

        host = self.get_parameter("ollama_host").value
        model = self.get_parameter("ollama_model").value
        hz = self.get_parameter("update_hz").value

        self._llm = OllamaClient(host=host, model=model, max_tokens=150)
        self._plan = {}
        self._exec = {}
        self._reflection = {}

        self._state = VolitionState()
        self._last_deliberation = time.time()

        self.create_subscription(String, "/grace/conscious/executive_plan",
                                 lambda m: self._set(m, "_plan"), 10)
        self.create_subscription(String, "/grace/conscious/central_executive",
                                 lambda m: self._set(m, "_exec"), 10)
        self.create_subscription(String, "/grace/conscious/reflection",
                                 lambda m: self._set(m, "_reflection"), 10)

        self._pub = self.create_publisher(String, "/grace/conscious/volition", 10)
        self.create_timer(1.0 / hz, self._update)
        self.get_logger().info("VolitionalControl (SLM) ready.")

    def _set(self, msg, attr):
        try:
            setattr(self, attr, json.loads(msg.data))
        except Exception:
            pass

    def _update(self):
        goal = self._plan.get("goal", "")
        steps = self._plan.get("steps", [])
        moral_cleared = self._plan.get("moral_cleared", True)
        priority = self._plan.get("priority", 0.5)
        exec_cmd = self._exec.get("command", "")
        mono = self._reflection.get("inner_monologue", "")
        symbolic = self._reflection.get("symbolic_conclusion", "")

        if not goal and not exec_cmd:
            return

        now = time.time()
        deliberation = now - self._last_deliberation
        self._last_deliberation = now

        prompt = (
            f"Goal: {goal}\n"
            f"Steps: {json.dumps(steps)}\n"
            f"Moral cleared: {moral_cleared}, Priority: {priority:.2f}\n"
            f"Executive command: {exec_cmd}\n"
            f"Monologue: {mono}\n"
            f"Conclusion: {symbolic}\n"
            f"Deliberation: {deliberation:.2f}s"
        )
        raw = self._llm.chat(prompt, system=SYSTEM_PROMPT)

        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = {
                "intention_formed": False, "intention_content": "",
                "agency_sense": 0.7, "deliberation_duration": deliberation,
                "decision_confidence": 0.5, "veto_power_active": False,
                "veto_reason": "",
            }

        self._state.intention_formed = parsed.get("intention_formed", False)
        self._state.intention_content = parsed.get("intention_content", "")
        self._state.agency_sense = max(0.0, min(1.0, parsed.get("agency_sense", 0.7)))
        self._state.deliberation_duration = max(0.0, parsed.get("deliberation_duration", deliberation))
        self._state.decision_confidence = max(0.0, min(1.0, parsed.get("decision_confidence", 0.5)))
        self._state.veto_power_active = parsed.get("veto_power_active", False)

        out = String()
        out.data = to_json(self._state)
        self._pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = VolitionalControlNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
