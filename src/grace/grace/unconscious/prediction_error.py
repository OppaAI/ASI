"""
grace_agi/unconscious/prediction_error.py
Precision-weights incoming errors and decides what reaches the thalamus.
"""
import json
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.utils.schemas import PredictionError, to_json

RELEVANCE_THRESHOLD = 0.25   # errors below this are discarded


class PredictionErrorNode(Node):
    def __init__(self):
        super().__init__("grace_prediction_error")
        self.create_subscription(String, "/grace/unconscious/prediction_errors",
                                 self._on_error, 10)
        self._pub_thal  = self.create_publisher(String, "/grace/unconscious/thalamic_broadcast", 10)
        self._pub_affect = self.create_publisher(String, "/grace/unconscious/affective_state", 10)
        self.get_logger().info("PredictionError ready.")

    def _on_error(self, msg: String):
        try:
            err = json.loads(msg.data)
        except Exception:
            return

        magnitude  = err.get("error_magnitude", 0.0)
        precision  = err.get("precision_weight", 1.0)
        weighted   = magnitude * precision

        # Pass to thalamus only if above relevance threshold
        if weighted >= RELEVANCE_THRESHOLD:
            out = String()
            out.data = msg.data   # forward unchanged
            self._pub_thal.publish(out)

        # Always update affective state (even small errors shift mood slightly)
        from grace.utils.schemas import AffectiveState
        import time
        arousal = min(1.0, weighted * 1.5)
        affect = AffectiveState(
            valence=max(0.0, 0.5 - magnitude * 0.3),
            arousal=arousal,
            dominance=0.5,
            emotion_label="alert" if arousal > 0.5 else "calm",
        )
        a_out = String()
        a_out.data = to_json(affect)
        self._pub_affect.publish(a_out)


def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(PredictionErrorNode())
    rclpy.shutdown()
