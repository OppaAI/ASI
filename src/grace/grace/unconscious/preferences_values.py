"""
grace_agi/unconscious/preferences_values.py
Learned priors encoding normative hierarchies and moral reasoning rules.
Persists to disk and receives updates from Conscience and Consolidation.
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.utils.memory_store import MemoryStore

DEFAULT_VALUES = {
    "care_for_life":       1.0,
    "honesty":             0.95,
    "helpfulness":         0.90,
    "curiosity":           0.90,
    "safety_first":        0.95,
    "respect_persons":     0.90,
    "environmental_care":  0.85,
    "obedience_to_owner":  0.80,
}


class PreferencesValuesNode(Node):
    def __init__(self):
        super().__init__("grace_preferences_values")
        self.declare_parameter("values_db", "/home/grace/memory/values.json")
        db_path = self.get_parameter("values_db").value
        self._store  = MemoryStore(db_path, max_entries=50)
        self._values = dict(DEFAULT_VALUES)
        saved = self._store.get("values")
        if saved:
            self._values.update(saved)

        self.create_subscription(String, "/grace/conscience/verdict",
                                 self._on_verdict, 10)
        self.create_subscription(String, "/grace/dreaming/consolidation",
                                 self._on_consolidation, 10)

        self._pub = self.create_publisher(String, "/grace/unconscious/values", 10)
        self.create_timer(5.0, self._broadcast)
        self.get_logger().info("PreferencesValues ready.")

    def _on_verdict(self, msg: String):
        try:
            v = json.loads(msg.data)
            # Immoral verdicts strengthen safety/care values slightly
            if v.get("verdict") == "immoral":
                self._values["safety_first"]  = min(1.0, self._values["safety_first"]  + 0.01)
                self._values["care_for_life"] = min(1.0, self._values["care_for_life"] + 0.01)
                self._store.set("values", self._values)
        except Exception:
            pass

    def _on_consolidation(self, msg: String):
        try:
            pkt = json.loads(msg.data)
            for k, v in pkt.get("value_updates", {}).items():
                if k in self._values:
                    self._values[k] = round(self._values[k] * 0.97 + v * 0.03, 4)
            self._store.set("values", self._values)
        except Exception:
            pass

    def _broadcast(self):
        out = String()
        out.data = json.dumps({"timestamp": time.time(), "values": self._values})
        self._pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = PreferencesValuesNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
