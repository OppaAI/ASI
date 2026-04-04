"""
grace_agi/unconscious/hyper_model.py
Meta-level controller that sets global epistemic depth and
precision weighting parameters for the whole predictive hierarchy.
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String

DEFAULT_PRECISION = {
    "global_confidence":  0.75,
    "epistemic_depth":    0.70,
    "field_evidencing":   0.65,
    "prior_strength":     0.60,
}


class HyperModelNode(Node):
    def __init__(self):
        super().__init__("grace_hyper_model")
        self._params = dict(DEFAULT_PRECISION)
        self._metacog = {}

        self.create_subscription(String, "/grace/conscious/metacognition",
                                 self._on_metacog, 10)

        self._pub_pred = self.create_publisher(String, "/grace/unconscious/precision", 10)
        self._pub_meta = self.create_publisher(String, "/grace/conscious/metacognition", 10)
        self.create_timer(4.0, self._broadcast)
        self.get_logger().info("HyperModel ready.")

    def _on_metacog(self, msg: String):
        try:
            d = json.loads(msg.data)
            conf = d.get("confidence_in_own_reasoning", 0.5)
            # When metacognition reports low confidence, reduce epistemic depth
            self._params["epistemic_depth"]   = round(0.5 + conf * 0.5, 3)
            self._params["global_confidence"] = round(conf, 3)
        except Exception:
            pass

    def _broadcast(self):
        out = String()
        out.data = json.dumps({"timestamp": time.time(), **self._params})
        self._pub_pred.publish(out)


def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(HyperModelNode())
    rclpy.shutdown()
