"""
grace_agi/conscience/esv_knowledge_base.py
Loads the ESV scripture principles YAML and broadcasts them to the
Moral Reasoning Engine. Purely rule-based — no LLM needed.
Follows the same pattern as moral_knowledge.py.
"""
import json, time, os
import yaml
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class ESVKnowledgeNode(Node):
    def __init__(self):
        super().__init__("grace_esv_knowledge")

        self.declare_parameter("scripture_path",
                               "/home/grace/config/scripture_principles.yaml")
        path = self.get_parameter("scripture_path").value

        self._principles = self._load(path)

        self._pub = self.create_publisher(String, "/grace/conscience/esv_knowledge", 10)
        self.create_timer(15.0, self._broadcast)
        self.get_logger().info(
            f"ESVKnowledge ready — {len(self._principles)} principles loaded.")

    def _load(self, path: str) -> list:
        candidates = [
            path,
            os.path.join(os.path.dirname(__file__), "../../config/scripture_principles.yaml"),
        ]
        for p in candidates:
            try:
                with open(os.path.expanduser(p)) as f:
                    data = yaml.safe_load(f)
                    return data.get("principles", data if isinstance(data, list) else [])
            except FileNotFoundError:
                continue
        self.get_logger().warn("ESVKnowledge: scripture file not found, using empty set.")
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
    node = ESVKnowledgeNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
