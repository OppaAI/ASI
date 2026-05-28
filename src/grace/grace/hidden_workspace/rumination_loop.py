"""
grace_agi/hidden_workspace/rumination_loop.py
Hidden Workspace — Rumination Loop
Rule-based system tracking repetitive negative thought patterns.
"""
import json
import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.utils.schemas import RuminationState, to_json
from math import exp


class RuminationLoopNode(Node):
    def __init__(self):
        super().__init__("grace_rumination_loop")

        self.declare_parameter("update_hz", 1.0)
        self.update_hz = self.get_parameter("update_hz").value

        self._intensity = 0.3
        self._negative_affect = 0.4
        self._stuckness = 0.3
        self._duration = 0.0
        self._worry_queue = []
        self._last_update = time.time()
        self._has_distraction = False
        self._workspace_focus = ""

        self.create_subscription(String, "/grace/unconscious/affective_state",
                                 self._on_affect, 10)
        self.create_subscription(String, "/grace/vital/pain_signal",
                                 self._on_pain, 10)
        self.create_subscription(String, "/grace/hidden/error_monitoring",
                                 self._on_error, 10)
        self.create_subscription(String, "/grace/conscious/global_workspace",
                                 self._on_workspace, 10)

        self._pub = self.create_publisher(String, "/grace/hidden/rumination", 10)
        self.create_timer(1.0 / self.update_hz, self._tick)
        self.get_logger().info("Rumination Loop ready.")

    def _on_affect(self, msg: String):
        try:
            d = json.loads(msg.data)
            valence = d.get("valence", 0.5)
            arousal = d.get("arousal", 0.3)
            self._negative_affect = max(self._negative_affect, (1.0 - valence) * arousal)
        except Exception:
            pass

    def _on_pain(self, msg: String):
        try:
            d = json.loads(msg.data)
            pain = d.get("pain_intensity", 0.0)
            if pain > 0.3:
                worry = {"content": f"pain:{d.get('pain_sources',['unknown'])[0]}",
                         "intensity": pain, "age": 0.0}
                self._worry_queue.append(worry)
        except Exception:
            pass

    def _on_error(self, msg: String):
        try:
            d = json.loads(msg.data)
            if d.get("error_detected", False):
                worry = {"content": f"error:{d.get('error_type','unknown')}",
                         "intensity": d.get("error_severity", 0.5), "age": 0.0}
                self._worry_queue.append(worry)
                self._stuckness = min(0.9, self._stuckness + d["error_severity"] * 0.2)
        except Exception:
            pass

    def _on_workspace(self, msg: String):
        try:
            d = json.loads(msg.data)
            self._workspace_focus = d.get("broadcast", "")
            # Novel, non-negative content can distract
            if self._workspace_focus and "negative" not in self._workspace_focus.lower():
                self._has_distraction = True
            else:
                self._has_distraction = False
        except Exception:
            pass

    def _tick(self):
        now = time.time()
        dt = now - self._last_update
        self._last_update = now

        if self._has_distraction and self._negative_affect < 0.6:
            distractor_strength = min(0.15, dt * 0.05)
            self._intensity = max(0.1, self._intensity - distractor_strength)
            self._stuckness = max(0.1, self._stuckness - distractor_strength * 0.5)
        else:
            rumination_feed = self._negative_affect * dt * 0.08
            self._intensity = min(0.95, self._intensity + rumination_feed)
            self._stuckness = min(0.9, self._stuckness + self._negative_affect * dt * 0.03)

        decay = exp(-0.02 * dt)
        self._intensity = max(0.1, self._intensity * decay)
        self._stuckness = max(0.1, self._stuckness * decay)

        self._duration += dt if self._intensity > 0.3 else 0.0

        new_queue = []
        for w in self._worry_queue:
            w["age"] += dt
            w["intensity"] *= exp(-0.01 * dt)
            if w["intensity"] > 0.1:
                new_queue.append(w)
        self._worry_queue = sorted(new_queue, key=lambda x: -x["intensity"])[:10]

        thought_loop = self._worry_queue[0]["content"] if self._worry_queue else ""
        state = RuminationState(
            timestamp=now,
            thought_loop_content=thought_loop,
            intensity=round(self._intensity, 3),
            negative_affect=round(self._negative_affect, 3),
            stuckness=round(self._stuckness, 3),
            duration_seconds=round(self._duration, 1),
            worry_queue=[w["content"] for w in self._worry_queue[:5]],
        )
        out = String()
        out.data = to_json(state)
        self._pub.publish(out)

        if self._intensity > 0.7 and int(now) % 5 == 0:
            self.get_logger().warn(
                f"High rumination: intensity={self._intensity:.2f} "
                f"stuck={self._stuckness:.2f} duration={self._duration:.0f}s"
            )


def main(args=None):
    rclpy.init(args=args)
    node = RuminationLoopNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
