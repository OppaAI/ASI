"""
grace_agi/hidden_workspace/active_suppression.py
Hidden Workspace — Active Thought Suppression
Rule-based system managing suppression with rebound effects.
"""
import json
import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.utils.schemas import ActiveSuppressionState, to_json
from math import exp


class ActiveSuppressionNode(Node):
    def __init__(self):
        super().__init__("grace_active_suppression")

        self.declare_parameter("update_hz", 1.0)
        self.update_hz = self.get_parameter("update_hz").value

        self._suppressed_thought = ""
        self._suppression_effort = 0.3
        self._rebound_intensity = 0.2
        self._suppression_success = 0.7
        self._cognitive_load = 0.2
        self._target_intensity = 0.0
        self._has_executive_plan = False
        self._last_update = time.time()

        self.create_subscription(String, "/grace/hidden/rumination",
                                 self._on_rumination, 10)
        self.create_subscription(String, "/grace/hidden/private_reflection",
                                 self._on_reflection, 10)
        self.create_subscription(String, "/grace/conscious/executive_plan",
                                 self._on_executive, 10)

        self._pub = self.create_publisher(String, "/grace/hidden/active_suppression", 10)
        self.create_timer(1.0 / self.update_hz, self._tick)
        self.get_logger().info("Active Suppression ready.")

    def _on_rumination(self, msg: String):
        try:
            d = json.loads(msg.data)
            intensity = d.get("intensity", 0.3)
            thought = d.get("thought_loop_content", "")
            if intensity > 0.5 and thought:
                self._target_intensity = intensity
                self._suppressed_thought = thought
        except Exception:
            pass

    def _on_reflection(self, msg: String):
        try:
            d = json.loads(msg.data)
            reflection = d.get("reflection_text", "")
            load = d.get("cognitive_load", 0.3)
            if reflection and load > 0.5:
                # Painful reflections may trigger active suppression
                self._suppressed_thought = reflection[:100]
                self._target_intensity = load
        except Exception:
            pass

    def _on_executive(self, msg: String):
        try:
            d = json.loads(msg.data)
            self._has_executive_plan = bool(d.get("steps", []))
        except Exception:
            pass

    def _tick(self):
        now = time.time()
        dt = now - self._last_update
        self._last_update = now

        if self._target_intensity > 0.4 and self._suppressed_thought:
            # Active suppression engaged
            self._suppression_effort = min(0.9, self._suppression_effort +
                                           self._target_intensity * dt * 0.15)
            self._cognitive_load = min(0.8, self._cognitive_load +
                                       self._suppression_effort * dt * 0.1)

            # Suppression success inversely related to intensity
            self._suppression_success = max(0.1, 1.0 - self._target_intensity * 0.6 -
                                            self._cognitive_load * 0.3)

            # Rebound builds as a function of effort
            self._rebound_intensity = min(0.9, self._rebound_intensity +
                                          self._suppression_effort * dt * 0.05)

            # Executive plan helps suppression
            if self._has_executive_plan:
                self._suppression_success = min(0.85, self._suppression_success + dt * 0.02)
                self._cognitive_load = max(0.1, self._cognitive_load - dt * 0.01)

            # If suppression fails, rebound spikes
            if self._suppression_success < 0.3:
                self._rebound_intensity = min(0.95, self._rebound_intensity + dt * 0.15)
                self._suppressed_thought = ""  # Thought breaks through
                self._target_intensity = 0.0
        else:
            # Natural decay
            decay = exp(-0.05 * dt)
            self._suppression_effort = max(0.1, self._suppression_effort * decay)
            self._rebound_intensity = max(0.05, self._rebound_intensity * decay)
            self._cognitive_load = max(0.1, self._cognitive_load * decay)
            self._suppression_success = min(0.8, self._suppression_success +
                                            (1.0 - self._suppression_success) * dt * 0.03)
            if self._suppression_effort < 0.15:
                self._suppressed_thought = ""

        self._suppression_effort = round(max(0.0, min(0.95, self._suppression_effort)), 3)
        self._rebound_intensity = round(max(0.0, min(0.95, self._rebound_intensity)), 3)
        self._suppression_success = round(max(0.0, min(0.95, self._suppression_success)), 3)
        self._cognitive_load = round(max(0.0, min(0.95, self._cognitive_load)), 3)

        state = ActiveSuppressionState(
            timestamp=now,
            thought_suppressed=self._suppressed_thought,
            suppression_effort=self._suppression_effort,
            rebound_intensity=self._rebound_intensity,
            suppression_success=self._suppression_success,
            cognitive_load=self._cognitive_load,
        )
        out = String()
        out.data = to_json(state)
        self._pub.publish(out)

        if self._rebound_intensity > 0.7 and int(now) % 3 == 0:
            self.get_logger().warn(
                f"Suppression rebound: {self._rebound_intensity:.2f} "
                f"effort={self._suppression_effort:.2f}"
            )


def main(args=None):
    rclpy.init(args=args)
    node = ActiveSuppressionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
