"""
grace_agi/unconscious/semantic_satiation.py
Unconscious Layer — Semantic Satiation
Repetition-induced meaning degradation · Concept accessibility tracking
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.utils.schemas import SemanticSatiationState, to_json


class SemanticSatiationNode(Node):
    def __init__(self):
        super().__init__("grace_semantic_satiation")

        self.declare_parameter("update_hz", 1.0)
        self.update_hz = self.get_parameter("update_hz").value
        self.declare_parameter("satiation_decay", 0.05)
        self._satiation_decay = self.get_parameter("satiation_decay").value

        self._satiation_level = 0.0
        self._target_concept = ""
        self._repetition_count = 0
        self._meaning_accessibility = 1.0
        self._recovery_progress = 0.0
        self._concept_counts = {}
        self._last_update = time.time()

        self.create_subscription(String, "/grace/conscious/global_workspace",
                                 self._on_global_workspace, 10)
        self.create_subscription(String, "/grace/unconscious/implicit_patterns",
                                 self._on_implicit_patterns, 10)

        self._pub = self.create_publisher(String, "/grace/unconscious/semantic_satiation", 10)
        self.create_timer(1.0 / self.update_hz, self._update_satiation)
        self.get_logger().info("Semantic Satiation ready.")

    def _on_global_workspace(self, msg: String):
        try:
            data = json.loads(msg.data)
            broadcast = data.get("broadcast", "")
            if broadcast:
                tokens = broadcast.lower().split()
                for token in tokens:
                    if len(token) > 3:
                        self._concept_counts[token] = self._concept_counts.get(token, 0) + 1
        except Exception as e:
            self.get_logger().warn(f"Failed to process global workspace: {e}")

    def _on_implicit_patterns(self, msg: String):
        try:
            data = json.loads(msg.data)
            pattern = data.get("pattern", "")
            if pattern:
                self._concept_counts[pattern] = self._concept_counts.get(pattern, 0) + 1
        except Exception as e:
            self.get_logger().warn(f"Failed to process implicit patterns: {e}")

    def _update_satiation(self):
        now_t = time.time()
        dt = now_t - self._last_update
        self._last_update = now_t

        if self._concept_counts:
            most_repeated = max(self._concept_counts, key=self._concept_counts.get)
            count = self._concept_counts[most_repeated]
            if most_repeated != self._target_concept:
                self._target_concept = most_repeated
                self._repetition_count = count
            else:
                self._repetition_count = count
        else:
            self._target_concept = ""
            self._repetition_count = 0

        expected_satiation = min(1.0, self._repetition_count * 0.1)
        if expected_satiation > self._satiation_level:
            self._satiation_level = expected_satiation
        else:
            self._satiation_level = max(0.0, self._satiation_level - self._satiation_decay * dt)

        self._meaning_accessibility = max(0.0, 1.0 - self._satiation_level)

        if self._repetition_count == 0 or self._satiation_level == 0.0:
            self._recovery_progress = 1.0
        else:
            self._recovery_progress = min(1.0, 1.0 - self._satiation_level)

        out = SemanticSatiationState(
            timestamp=now_t,
            satiation_level=self._satiation_level,
            target_concept=self._target_concept,
            repetition_count=self._repetition_count,
            meaning_accessibility=self._meaning_accessibility,
            recovery_progress=self._recovery_progress,
        )
        msg = String()
        msg.data = to_json(out)
        self._pub.publish(msg)

        if int(now_t) % 10 == 0:
            self.get_logger().info(
                f"Satiation - concept:{self._target_concept} "
                f"sat:{self._satiation_level:.2f} "
                f"access:{self._meaning_accessibility:.2f} "
                f"reps:{self._repetition_count}"
            )


def main(args=None):
    rclpy.init(args=args)
    node = SemanticSatiationNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
