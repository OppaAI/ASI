"""
grace_agi/conscious/salience_network.py
Attention switching and emotional tagging.
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.utils.schemas import GlobalWorkspaceContent, to_json


class SalienceNetworkNode(Node):
    def __init__(self):
        super().__init__("grace_salience_network")
        self._affect = {}
        self._bundle = {}

        self.create_subscription(String, "/grace/unconscious/affective_state",
                                 lambda m: self._set(m, "_affect"), 10)
        self.create_subscription(String, "/grace/sensors/bundle",
                                 lambda m: self._set(m, "_bundle"), 10)

        self._pub = self.create_publisher(String, "/grace/conscious/salience", 10)
        self.create_timer(1.0, self._tick)
        self.get_logger().info("SalienceNetwork ready.")

    def _set(self, msg, attr):
        try: setattr(self, attr, json.loads(msg.data))
        except Exception: pass

    def _tick(self):
        arousal  = self._affect.get("arousal", 0.3)
        lidar    = self._bundle.get("lidar_nearest_m", 99.0)
        audio    = self._bundle.get("audio_text", "")
        social   = self._bundle.get("social_cues", "")

        salience = arousal * 0.4
        content  = "ambient"

        if lidar < 1.0:
            salience = max(salience, 0.9)
            content  = f"obstacle at {lidar:.2f}m"
        elif audio:
            salience = max(salience, 0.6)
            content  = f"audio: {audio[:40]}"
        elif social:
            salience = max(salience, 0.7)
            content  = f"social: {social[:40]}"

        gw = GlobalWorkspaceContent(
            broadcast=f"Salience switch: {content}",
            sources=["salience_network"],
            salience=round(salience, 3),
        )
        out = String(); out.data = to_json(gw)
        self._pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(SalienceNetworkNode())
    rclpy.shutdown()
