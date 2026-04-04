"""
grace_agi/conscience/moral_knowledge.py
Loads the scripture principles YAML and broadcasts them to the
Moral Reasoning Engine. Purely rule-based — no LLM needed.
"""
import json, time, os
import yaml
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class MoralKnowledgeNode(Node):
    def __init__(self):
        super().__init__("grace_moral_knowledge")

        self.declare_parameter("scripture_path",
                               "/home/grace/config/scripture_principles.yaml")
        path = self.get_parameter("scripture_path").value

        self._principles = self._load(path)

        self._pub = self.create_publisher(String, "/grace/conscience/knowledge", 10)
        self.create_timer(10.0, self._broadcast)   # re-broadcast every 10s
        self.get_logger().info(
            f"MoralKnowledge ready — {len(self._principles)} principles loaded.")

    def _load(self, path: str) -> list:
        # Try the provided path first, then fall back to package config dir
        candidates = [
            path,
            os.path.join(os.path.dirname(__file__), "../../config/scripture_principles.yaml"),
        ]
        for p in candidates:
            try:
                with open(os.path.expanduser(p)) as f:
                    data = yaml.safe_load(f)
                    return data.get("principles", [])
            except FileNotFoundError:
                continue
        self.get_logger().warn("MoralKnowledge: scripture file not found, using empty set.")
        return []

    def _broadcast(self):
        out = String()
        out.data = json.dumps({
            "timestamp":  time.time(),
            "principles": self._principles,
        })
        self._pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = MoralKnowledgeNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
