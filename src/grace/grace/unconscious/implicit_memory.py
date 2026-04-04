"""
grace_agi/unconscious/implicit_memory.py
Captures automatic associations from sensor bundles and primes
subconscious memory systems.
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.utils.schemas import MemoryEntry, to_json


class ImplicitMemoryNode(Node):
    def __init__(self):
        super().__init__("grace_implicit_memory")
        self._priming_buffer = []

        self.create_subscription(String, "/grace/sensors/bundle",
                                 self._on_sensor, 10)

        # Publish primed patterns to each subconscious subsystem
        self._pub_episodic   = self.create_publisher(String, "/grace/subconscious/episodic",   10)
        self._pub_semantic   = self.create_publisher(String, "/grace/subconscious/semantic",   10)
        self._pub_procedural = self.create_publisher(String, "/grace/subconscious/procedural", 10)
        self._pub_social     = self.create_publisher(String, "/grace/subconscious/social",     10)

        self.create_timer(3.0, self._flush)
        self.get_logger().info("ImplicitMemory ready.")

    def _on_sensor(self, msg: String):
        try:
            bundle = json.loads(msg.data)
            # Capture notable signals as implicit associations
            if bundle.get("camera_description"):
                self._priming_buffer.append({
                    "type": "visual", "content": bundle["camera_description"],
                    "timestamp": bundle.get("timestamp", time.time())
                })
            if bundle.get("social_cues"):
                self._priming_buffer.append({
                    "type": "social", "content": bundle["social_cues"],
                    "timestamp": bundle.get("timestamp", time.time())
                })
        except Exception:
            pass

    def _flush(self):
        for item in self._priming_buffer:
            entry = MemoryEntry(
                memory_type=item["type"],
                content=item["content"],
                tags=[item["type"], "implicit"],
                timestamp=item["timestamp"],
            )
            s = String(); s.data = to_json(entry)
            if item["type"] == "social":
                self._pub_social.publish(s)
            else:
                self._pub_episodic.publish(s)
                self._pub_semantic.publish(s)
        self._priming_buffer.clear()


def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(ImplicitMemoryNode())
    rclpy.shutdown()
