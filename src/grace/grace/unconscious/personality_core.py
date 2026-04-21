"""
grace_agi/unconscious/personality_core.py
Stable trait biases that modulate downstream processing.
Persists to disk and updates slowly via consolidation.
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.grace.utils.schemas import to_json
from grace.grace.utils.memory_store import MemoryStore

DEFAULT_TRAITS = {
    "openness":          0.85,
    "conscientiousness": 0.80,
    "extraversion":      0.50,
    "agreeableness":     0.90,
    "neuroticism":       0.20,
    "curiosity":         0.95,   # GRACE-specific
}


class PersonalityCoreNode(Node):
    def __init__(self):
        super().__init__("grace_personality_core")
        self.declare_parameter("personality_db", "/home/grace/memory/personality.json")
        db_path = self.get_parameter("personality_db").value
        self._store  = MemoryStore(db_path, max_entries=50)
        self._traits = dict(DEFAULT_TRAITS)
        saved = self._store.get("traits")
        if saved:
            self._traits.update(saved)

        # Absorb consolidation updates
        self.create_subscription(String, "/grace/dreaming/consolidation",
                                 self._on_consolidation, 10)

        self._pub = self.create_publisher(String, "/grace/unconscious/personality", 10)
        self.create_timer(5.0, self._broadcast)
        self.get_logger().info("PersonalityCore ready.")

    def _on_consolidation(self, msg: String):
        try:
            pkt = json.loads(msg.data)
            deltas = pkt.get("personality_deltas", {})
            for k, v in deltas.items():
                if k in self._traits:
                    # Slow update — personality changes very gradually
                    self._traits[k] = round(self._traits[k] * 0.98 + v * 0.02, 4)
            self._store.set("traits", self._traits)
        except Exception:
            pass

    def _broadcast(self):
        out = String()
        out.data = json.dumps({"timestamp": time.time(), "traits": self._traits})
        self._pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = PersonalityCoreNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
