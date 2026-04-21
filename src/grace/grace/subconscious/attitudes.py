"""
grace_agi/subconscious/attitudes.py
Evaluative dispositions and cognitive dissonance resolution.
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.grace.utils.schemas import AttitudeState, to_json

DEFAULT_ATTITUDES = {
    "wildlife":       0.95,
    "photography":    0.90,
    "humans":         0.80,
    "obstacles":     -0.70,
    "rain":          -0.30,
    "open_spaces":    0.85,
    "helping_others": 0.90,
}


class AttitudesNode(Node):
    def __init__(self):
        super().__init__("grace_attitudes")
        self._evaluations = dict(DEFAULT_ATTITUDES)
        self._dissonance  = 0.0

        self.create_subscription(String, "/grace/unconscious/affective_state",
                                 self._on_affect, 10)
        self.create_subscription(String, "/grace/conscience/verdict",
                                 self._on_verdict, 10)
        self.create_subscription(String, "/grace/action/log",
                                 self._on_action, 10)

        self._pub = self.create_publisher(String, "/grace/subconscious/attitudes", 10)
        self.create_timer(5.0, self._broadcast)
        self.get_logger().info("Attitudes ready.")

    def _on_affect(self, msg: String):
        try:
            d = json.loads(msg.data)
            # High arousal + negative valence increases dissonance
            v = d.get("valence", 0.5)
            a = d.get("arousal", 0.3)
            if v < 0.4 and a > 0.6:
                self._dissonance = min(1.0, self._dissonance + 0.05)
            else:
                self._dissonance = max(0.0, self._dissonance - 0.02)
        except Exception: pass

    def _on_verdict(self, msg: String):
        try:
            v = json.loads(msg.data)
            if v.get("verdict") == "immoral":
                # Strengthen negative attitude toward the flagged situation
                situation = v.get("situation", "")[:30]
                self._evaluations[situation] = max(-1.0,
                    self._evaluations.get(situation, 0.0) - 0.1)
                self._dissonance = min(1.0, self._dissonance + 0.1)
        except Exception: pass

    def _on_action(self, msg: String):
        # Successful actions slightly reinforce relevant attitudes
        pass

    def _broadcast(self):
        state = AttitudeState(
            evaluations=self._evaluations,
            dissonance_level=round(self._dissonance, 3),
        )
        out = String(); out.data = to_json(state)
        self._pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(AttitudesNode())
    rclpy.shutdown()
