"""
grace_agi/qualia/flow_state_detector.py
Non-SLM node — Flow State Detector.
Detects flow state based on challenge-skill balance, concentration, affective
arousal, and loss of self-consciousness. Uses executive plan difficulty and
circadian alertness to determine flow probability.
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String

from grace.utils.schemas import FlowState, to_json


class FlowStateDetectorNode(Node):
    def __init__(self):
        super().__init__("grace_flow_state_detector")

        self.declare_parameter("update_hz", 1.0)
        hz = self.get_parameter("update_hz").value

        self._plan = {}
        self._affect = {}
        self._metacog = {}
        self._circadian = {}

        self._state = FlowState()
        self._task_difficulty_history: list[float] = []

        self.create_subscription(String, "/grace/conscious/executive_plan",
                                 self._on_plan, 10)
        self.create_subscription(String, "/grace/unconscious/affective_state",
                                 lambda m: self._set(m, "_affect"), 10)
        self.create_subscription(String, "/grace/conscious/metacognition",
                                 lambda m: self._set(m, "_metacog"), 10)
        self.create_subscription(String, "/grace/vital/circadian_rhythm",
                                 lambda m: self._set(m, "_circadian"), 10)

        self._pub = self.create_publisher(String, "/grace/qualia/flow", 10)
        self.create_timer(1.0 / hz, self._update)
        self.get_logger().info("FlowStateDetector ready.")

    def _set(self, msg, attr):
        try:
            setattr(self, attr, json.loads(msg.data))
        except Exception:
            pass

    def _on_plan(self, msg: String):
        try:
            self._plan = json.loads(msg.data)
            priority = self._plan.get("priority", 0.5)
            steps = self._plan.get("steps", [])
            difficulty = min(1.0, priority * 0.7 + len(steps) * 0.05)
            self._task_difficulty_history.append(difficulty)
            self._task_difficulty_history = self._task_difficulty_history[-20:]
        except Exception:
            pass

    def _update(self):
        arousal = self._affect.get("arousal", 0.3)
        valence = self._affect.get("valence", 0.5)
        attention = self._circadian.get("attention", 0.6)
        energy = self._circadian.get("energy", 0.6)
        confidence = self._metacog.get("confidence_in_own_reasoning", 0.5)

        avg_difficulty = 0.5
        if self._task_difficulty_history:
            avg_difficulty = sum(self._task_difficulty_history) / len(self._task_difficulty_history)

        self._state.challenge_skill_balance = max(0.0, min(1.0,
            1.0 - abs(avg_difficulty - (arousal * 0.5 + confidence * 0.5))))

        self._state.concentration_level = max(0.0, min(1.0,
            attention * 0.5 + energy * 0.3 + (1.0 - arousal * 0.5) * 0.2))

        self._state.loss_of_self_consciousness = max(0.0, min(1.0,
            self._state.concentration_level * 0.6 - valence * 0.1))

        self._state.time_distortion = max(0.0, min(1.0,
            self._state.challenge_skill_balance * 0.5 + arousal * 0.3))

        self._state.autotelic_experience = max(0.0, min(1.0,
            self._state.challenge_skill_balance * 0.6 + valence * 0.3))

        flow_threshold = 0.6
        self._state.in_flow = (
            self._state.challenge_skill_balance > flow_threshold
            and self._state.concentration_level > flow_threshold
            and self._state.loss_of_self_consciousness > 0.3
        )

        out = String()
        out.data = to_json(self._state)
        self._pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = FlowStateDetectorNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
