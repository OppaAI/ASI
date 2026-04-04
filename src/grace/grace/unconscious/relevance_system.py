"""
grace_agi/unconscious/relevance_system.py
Computes a relevance score for current content and gates GW access.
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.utils.schemas import RelevanceScore, GlobalWorkspaceContent, to_json

GW_RELEVANCE_THRESHOLD = 0.5


class RelevanceSystemNode(Node):
    def __init__(self):
        super().__init__("grace_relevance_system")
        self._affect  = {}
        self._reward  = {}
        self._bundle  = {}

        self.create_subscription(String, "/grace/unconscious/affective_state",
                                 lambda m: self._set(m, "_affect"), 10)
        self.create_subscription(String, "/grace/unconscious/reward",
                                 lambda m: self._set(m, "_reward"), 10)
        self.create_subscription(String, "/grace/sensors/bundle",
                                 lambda m: self._set(m, "_bundle"), 10)

        self._pub_rel = self.create_publisher(String, "/grace/unconscious/relevance", 10)
        self._pub_gw  = self.create_publisher(String, "/grace/conscious/global_workspace", 10)
        self.create_timer(1.0, self._tick)
        self.get_logger().info("RelevanceSystem ready.")

    def _set(self, msg, attr):
        try: setattr(self, attr, json.loads(msg.data))
        except Exception: pass

    def _tick(self):
        arousal  = self._affect.get("arousal", 0.3)
        reward   = abs(self._reward.get("value", 0.0))
        lidar    = self._bundle.get("lidar_nearest_m", 99.0)
        obstacle = max(0.0, 1.0 - lidar / 3.0)

        score   = round((arousal * 0.4 + reward * 0.3 + obstacle * 0.3), 3)
        content = (self._bundle.get("camera_description", "") or
                   self._bundle.get("audio_text", "current environment"))

        rel = RelevanceScore(content=content, score=score,
                             motive="safety" if obstacle > 0.5 else "curiosity")
        r_out = String(); r_out.data = to_json(rel)
        self._pub_rel.publish(r_out)

        if score >= GW_RELEVANCE_THRESHOLD:
            gw = GlobalWorkspaceContent(
                broadcast=f"Relevance alert [{score:.2f}]: {content[:80]}",
                sources=["relevance_system"],
                salience=score,
            )
            g_out = String(); g_out.data = to_json(gw)
            self._pub_gw.publish(g_out)


def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(RelevanceSystemNode())
    rclpy.shutdown()
