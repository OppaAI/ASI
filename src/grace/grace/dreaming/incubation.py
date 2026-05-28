"""
grace_agi/dreaming/incubation.py
Non-SLM node — Incubation.
Models unconscious incubation of unsolved problems with spreading activation
that can lead to sudden insight.
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String

from grace.utils.schemas import IncubationState, to_json


class IncubationNode(Node):
    def __init__(self):
        super().__init__("grace_incubation")

        self.declare_parameter("update_hz", 3.0)
        hz = self.get_parameter("update_hz").value

        self._problems: list[dict] = []
        self._reflection: dict = {}
        self._activation: dict[str, float] = {}
        self._durations: dict[str, float] = {}
        self._insight_threshold: float = 0.85

        self.create_subscription(String, "/grace/conscious/executive_plan",
                                 self._on_executive_plan, 10)
        self.create_subscription(String, "/grace/conscious/reflection",
                                 self._on_reflection, 10)

        self._pub = self.create_publisher(String, "/grace/dreaming/incubation", 10)
        self.create_timer(1.0 / hz, self._process)
        self.get_logger().info("Incubation ready.")

    def _on_executive_plan(self, msg: String):
        try:
            plan = json.loads(msg.data)
            goal = plan.get("goal", "")
            if goal and goal not in self._activation:
                entry = {"goal": goal, "steps": plan.get("steps", []),
                         "timestamp": time.time()}
                self._problems.append(entry)
                self._activation[goal] = 0.1
                self._durations[goal] = 0.0
                if len(self._problems) > 10:
                    old = self._problems.pop(0)
                    self._activation.pop(old["goal"], None)
                    self._durations.pop(old["goal"], None)
        except Exception:
            pass

    def _on_reflection(self, msg: String):
        try:
            self._reflection = json.loads(msg.data)
            content = self._reflection.get("inner_monologue", "")
            for prob in self._problems:
                goal = prob["goal"]
                if any(w in content.lower() for w in goal.lower().split()[:3]):
                    self._activation[goal] = min(1.0, self._activation.get(goal, 0.0) + 0.05)
        except Exception:
            pass

    def _process(self):
        now = time.time()
        emerging_insights = []

        for prob in self._problems:
            goal = prob["goal"]
            self._durations[goal] = self._durations.get(goal, 0.0) + (1.0 / 3.0)

            age = now - prob.get("timestamp", now)
            base_activation = min(0.5, age / 300.0)
            random_boost = ((hash(goal + str(int(now * 2))) & 0xFFFF) / 65535.0) * 0.1
            self._activation[goal] = min(1.0, base_activation + random_boost +
                                         self._activation.get(goal, 0.0) * 0.95)

            if self._activation[goal] >= self._insight_threshold:
                emerging_insights.append(goal)

        for goal in emerging_insights:
            duration = self._durations.get(goal, 0.0)

            state = IncubationState(
                incubation_active=False,
                problem_content=goal,
                incubation_duration=duration,
                background_processing=(
                    f"Spreading activation reached threshold "
                    f"({self._activation[goal]:.2f}) after {duration:.0f}s"),
                insight_emerging=True,
                activation_spreading=self._activation[goal],
            )
            out = String(); out.data = to_json(state)
            self._pub.publish(out)
            self.get_logger().info(f"Insight emerging: {goal[:50]}")

            self._activation[goal] = 0.0
            self._durations[goal] = 0.0

        if not emerging_insights and self._problems:
            prob = self._problems[-1]
            state = IncubationState(
                incubation_active=True,
                problem_content=prob["goal"],
                incubation_duration=self._durations.get(prob["goal"], 0.0),
                background_processing=(
                    f"Background spreading activation: "
                    f"{self._activation.get(prob['goal'], 0.0):.2f}/{self._insight_threshold:.2f}"),
                insight_emerging=False,
                activation_spreading=self._activation.get(prob["goal"], 0.0),
            )
            out = String(); out.data = to_json(state)
            self._pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = IncubationNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
