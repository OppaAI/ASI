"""
grace_agi/conscious/working_memory.py
Phonological loop + visuospatial sketchpad + active thought buffer.
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.grace.utils.schemas import to_json
from collections import deque

BUFFER_SIZE = 7   # Miller's law


class WorkingMemoryNode(Node):
    def __init__(self):
        super().__init__("grace_working_memory")

        self._phonological: deque = deque(maxlen=BUFFER_SIZE)   # verbal items
        self._visuospatial: deque = deque(maxlen=BUFFER_SIZE)   # spatial items
        self._active_thought = ""

        self.create_subscription(String, "/grace/conscious/global_workspace",
                                 self._on_gw, 10)
        self.create_subscription(String, "/grace/action/log",
                                 self._on_action, 10)

        self._pub = self.create_publisher(String, "/grace/conscious/working_memory", 10)
        self.create_timer(1.0, self._broadcast)
        self.get_logger().info("WorkingMemory ready.")

    def _on_gw(self, msg: String):
        try:
            gw = json.loads(msg.data)
            broadcast = gw.get("broadcast", "")
            if broadcast:
                self._active_thought = broadcast
                self._phonological.append(broadcast[:80])
        except Exception: pass

    def _on_action(self, msg: String):
        try:
            d = json.loads(msg.data)
            action = d.get("action", msg.data)
            self._phonological.append(f"Did: {action[:60]}")
        except Exception:
            self._phonological.append(msg.data[:60])

    def _broadcast(self):
        out = String()
        out.data = json.dumps({
            "timestamp":        time.time(),
            "active_thought":   self._active_thought,
            "phonological":     list(self._phonological),
            "visuospatial":     list(self._visuospatial),
        })
        self._pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(WorkingMemoryNode())
    rclpy.shutdown()
