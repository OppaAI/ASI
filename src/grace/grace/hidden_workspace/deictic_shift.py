"""
grace_agi/hidden_workspace/deictic_shift.py
Hidden Workspace — Deictic Shift System
Rule-based perspective switching (self/other/observer/past/future).
"""
import json
import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.utils.schemas import DeicticShiftState, to_json


PERSPECTIVES = ["self", "other", "observer", "past_self", "future_self"]


class DeicticShiftNode(Node):
    def __init__(self):
        super().__init__("grace_deictic_shift")

        self.declare_parameter("update_hz", 0.5)
        self.update_hz = self.get_parameter("update_hz").value

        self._current_perspective = "self"
        self._shift_count = 0
        self._cognitive_flexibility = 0.5
        self._empathy_access = 0.4
        self._temporal_shift_capacity = 0.6
        self._shift_cooldown = 0.0
        self._last_update = time.time()
        self._reflection_perspective_triggers = []
        self._conscious_reflection_triggers = []

        self.create_subscription(String, "/grace/conscious/reflection",
                                 self._on_reflection, 10)
        self.create_subscription(String, "/grace/hidden/private_reflection",
                                 self._on_private_reflection, 10)

        self._pub = self.create_publisher(String, "/grace/hidden/deictic_shift", 10)
        self.create_timer(1.0 / self.update_hz, self._tick)
        self.get_logger().info("Deictic Shift ready.")

    def _on_reflection(self, msg: String):
        try:
            d = json.loads(msg.data)
            text = d.get("inner_monologue", "")
            symbolic = d.get("symbolic_conclusion", "")
            combined = (text + " " + symbolic).lower()
            triggers = []
            if "they" in combined or "them" in combined or "their" in combined:
                triggers.append("other")
            if "someone" in combined or "people" in combined or "observer" in combined:
                triggers.append("observer")
            if "past" in combined or "before" in combined or "remember" in combined:
                triggers.append("past_self")
            if "future" in combined or "will" in combined or "plan" in combined:
                triggers.append("future_self")
            if triggers:
                self._conscious_reflection_triggers.extend(triggers)
        except Exception:
            pass

    def _on_private_reflection(self, msg: String):
        try:
            d = json.loads(msg.data)
            text = d.get("reflection_text", "").lower()
            if "other" in text or "they" in text:
                self._reflection_perspective_triggers.append("other")
                self._empathy_access = min(0.9, self._empathy_access + 0.05)
        except Exception:
            pass

    def _maybe_shift_perspective(self):
        all_triggers = (self._conscious_reflection_triggers +
                        self._reflection_perspective_triggers)
        if not all_triggers or self._shift_cooldown > 0:
            return

        trigger_counts = {}
        for t in all_triggers:
            if t in PERSPECTIVES:
                trigger_counts[t] = trigger_counts.get(t, 0) + 1

        if not trigger_counts:
            return

        # Shift to the most triggered perspective that is not current
        best_perspective = max(trigger_counts, key=trigger_counts.get)
        if best_perspective != self._current_perspective:
            self._current_perspective = best_perspective
            self._shift_count += 1
            self._shift_cooldown = 5.0  # seconds before next shift
            # Each shift increases flexibility
            self._cognitive_flexibility = min(0.95, self._cognitive_flexibility + 0.02)
            self._empathy_access = min(0.95, self._empathy_access + 0.03)

    def _tick(self):
        now = time.time()
        dt = now - self._last_update
        self._last_update = now

        self._shift_cooldown = max(0.0, self._shift_cooldown - dt)

        self._maybe_shift_perspective()

        # Natural drift back to self perspective over time
        if self._shift_cooldown <= 0 and self._current_perspective != "self":
            decay = dt * 0.02
            if decay > 0:
                self._current_perspective = "self"

        # Decay flexibility and empathy toward baseline if not shifting
        if self._shift_cooldown <= 0:
            self._cognitive_flexibility = max(0.3, self._cognitive_flexibility - dt * 0.01)
            self._empathy_access = max(0.2, self._empathy_access - dt * 0.005)

        # Temporal shift capacity grows with practice
        self._temporal_shift_capacity = min(0.9, 0.6 + self._shift_count * 0.005)

        # Clear old triggers
        self._conscious_reflection_triggers.clear()
        self._reflection_perspective_triggers.clear()

        state = DeicticShiftState(
            timestamp=now,
            current_perspective=self._current_perspective,
            shift_count=self._shift_count,
            cognitive_flexibility=round(self._cognitive_flexibility, 3),
            empathy_access=round(self._empathy_access, 3),
            temporal_shift_capacity=round(self._temporal_shift_capacity, 3),
        )
        out = String()
        out.data = to_json(state)
        self._pub.publish(out)

        if int(now) % 15 == 0:
            self.get_logger().info(
                f"Perspective: {self._current_perspective} "
                f"shifts={self._shift_count} "
                f"flex={self._cognitive_flexibility:.2f}"
            )


def main(args=None):
    rclpy.init(args=args)
    node = DeicticShiftNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
