"""
grace_agi/unconscious/reward_motivation.py
Dopaminergic-like reward signal computation.
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.grace.utils.schemas import RewardSignal, to_json


class RewardMotivationNode(Node):
    def __init__(self):
        super().__init__("grace_reward_motivation")
        self._affect = {}
        self._last_action = ""
        self.create_subscription(String, "/grace/unconscious/affective_state",
                                 lambda m: self._set(m, "_affect"), 10)
        self.create_subscription(String, "/grace/action/log",
                                 self._on_action, 10)
        self._pub = self.create_publisher(String, "/grace/unconscious/reward", 10)
        self.create_timer(2.0, self._tick)
        self.get_logger().info("RewardMotivation ready.")

    def _set(self, msg, attr):
        try: setattr(self, attr, json.loads(msg.data))
        except Exception: pass

    def _on_action(self, msg: String):
        self._last_action = msg.data

    def _tick(self):
        valence = self._affect.get("valence", 0.5)
        arousal = self._affect.get("arousal", 0.3)
        # Reward = positive valence and low threat arousal
        value  = (valence - 0.5) * 2.0          # -1 to +1
        approach = value >= 0
        sig = RewardSignal(value=round(value, 3), source="affective", approach=approach)
        out = String(); out.data = to_json(sig)
        self._pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(RewardMotivationNode())
    rclpy.shutdown()
