"""
grace_agi/conscious/central_executive.py
SLM node — Central Executive Network.
Planning, goal management, and cognitive control.
Proposes action plans — subject to moral veto from ConscienceCore.
Interfaces with Nav2 for navigation goals.
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import PoseStamped

from grace.utils.schemas import ExecutivePlan, to_json
from grace.utils.ollama_client import OllamaClient

SYSTEM_PROMPT = """You are GRACE's central executive — the planner and goal manager.
Given the current global workspace, metacognition assessment, values, and
available skills, produce an action plan as JSON:
{
  "goal":     str (max 40 words),
  "steps":    [{"action": str, "params": {}}],
  "priority": float 0-1,
  "rationale": str (max 30 words)
}
Reply ONLY with the JSON.
Available actions: navigate_to_pose, take_photo, speak, wait, return_home, avoid_obstacle, greet_person."""


class CentralExecutiveNode(Node):
    def __init__(self):
        super().__init__("grace_central_executive")

        self.declare_parameter("ollama_host",  "http://localhost:11434")
        self.declare_parameter("ollama_model", "nemotron")
        self.declare_parameter("conscious_hz", 1.0)

        host  = self.get_parameter("ollama_host").value
        model = self.get_parameter("ollama_model").value
        hz    = self.get_parameter("conscious_hz").value

        self._llm     = OllamaClient(host=host, model=model, max_tokens=300)
        self._gw      = {}
        self._meta    = {}
        self._values  = {}
        self._verdict = {}
        self._skills  = []
        self._blocked = False

        self.create_subscription(String, "/grace/conscious/global_workspace",
                                 lambda m: self._set(m, "_gw"),      10)
        self.create_subscription(String, "/grace/conscious/metacognition",
                                 lambda m: self._set(m, "_meta"),    10)
        self.create_subscription(String, "/grace/unconscious/values",
                                 lambda m: self._set(m, "_values"),  10)
        self.create_subscription(String, "/grace/subconscious/procedural_recall",
                                 self._on_skills, 10)
        self.create_subscription(String, "/grace/conscience/verdict",
                                 self._on_verdict, 10)

        self._pub_plan  = self.create_publisher(String,      "/grace/conscious/executive_plan", 10)
        self._pub_action = self.create_publisher(String,     "/grace/action/log",               10)

        self.create_timer(1.0 / hz, self._plan)
        self.get_logger().info("CentralExecutive (SLM) ready.")

    def _set(self, msg, attr):
        try: setattr(self, attr, json.loads(msg.data))
        except Exception: pass

    def _on_skills(self, msg: String):
        try:
            d = json.loads(msg.data)
            self._skills = [s.get("skill", "") for s in d.get("skills", [])]
        except Exception: pass

    def _on_verdict(self, msg: String):
        try:
            v = json.loads(msg.data)
            self._blocked = v.get("block_action", False)
            if self._blocked:
                self.get_logger().warn(
                    f"Executive blocked by Conscience: {v.get('reasoning','')[:80]}")
        except Exception: pass

    def _plan(self):
        if self._blocked:
            self._blocked = False   # reset each cycle; conscience re-evaluates
            return

        broadcast = self._gw.get("broadcast", "")
        if not broadcast:
            return

        conf = self._meta.get("confidence_in_own_reasoning", 0.5)
        top_values = sorted(
            self._values.get("values", {}).items(),
            key=lambda x: x[1], reverse=True)[:3]
        value_str = ", ".join(f"{k}={v:.2f}" for k, v in top_values)

        prompt = (f"Current situation: {broadcast}\n"
                  f"Reasoning confidence: {conf:.2f}\n"
                  f"Top values: {value_str}\n"
                  f"Available skills: {', '.join(self._skills[:6])}")

        raw = self._llm.chat(prompt, system=SYSTEM_PROMPT)
        try:
            parsed = json.loads(raw)
        except Exception:
            return  # malformed — skip cycle

        plan = ExecutivePlan(
            goal=parsed.get("goal", ""),
            steps=parsed.get("steps", []),
            moral_cleared=True,
            priority=parsed.get("priority", 0.5),
        )

        # Publish plan (Conscience will evaluate it and may block next cycle)
        p_out = String(); p_out.data = to_json(plan)
        self._pub_plan.publish(p_out)

        # Log the top action
        if plan.steps:
            a_out = String()
            a_out.data = json.dumps({
                "action":    plan.steps[0].get("action", ""),
                "params":    plan.steps[0].get("params", {}),
                "goal":      plan.goal,
                "timestamp": time.time(),
            })
            self._pub_action.publish(a_out)


def main(args=None):
    rclpy.init(args=args)
    node = CentralExecutiveNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
