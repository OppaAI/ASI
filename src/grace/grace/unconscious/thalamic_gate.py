"""
grace_agi/unconscious/thalamic_gate.py
Controls access to the Global Workspace — only high-relevance signals pass.
"""
import json
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.utils.schemas import to_json

GW_THRESHOLD = 0.35


class ThalamicGateNode(Node):
    def __init__(self):
        super().__init__("grace_thalamic_gate")
        self.create_subscription(String, "/grace/unconscious/thalamic_broadcast",
                                 self._on_signal, 10)
        self._pub_gw = self.create_publisher(String, "/grace/conscious/global_workspace", 10)
        self.get_logger().info("ThalamicGate ready.")

    def _on_signal(self, msg: String):
        try:
            d = json.loads(msg.data)
        except Exception:
            return
        if d.get("error_magnitude", 0.0) * d.get("precision_weight", 1.0) >= GW_THRESHOLD:
            # Wrap as Global Workspace content
            from grace.utils.schemas import GlobalWorkspaceContent
            gw = GlobalWorkspaceContent(
                broadcast=f"Thalamic gate promoted: {d.get('source','?')} error={d.get('error_magnitude',0):.2f}",
                sources=["thalamic_gate"],
                salience=d.get("error_magnitude", 0.5),
            )
            out = String()
            out.data = to_json(gw)
            self._pub_gw.publish(out)


def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(ThalamicGateNode())
    rclpy.shutdown()
