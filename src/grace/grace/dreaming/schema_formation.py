"""
grace_agi/dreaming/schema_formation.py
Non-SLM node — Schema Formation.
Forms abstract schemas from multiple concrete episodic and semantic instances.
Tracks abstraction level, predictive power, and flexibility.
"""
import json, time, hashlib, rclpy
from rclpy.node import Node
from std_msgs.msg import String

from grace.utils.schemas import SchemaState, to_json


class SchemaFormationNode(Node):
    def __init__(self):
        super().__init__("grace_schema_formation")

        self.declare_parameter("update_hz", 5.0)
        hz = self.get_parameter("update_hz").value

        self._episodic_buffer: list[dict] = []
        self._semantic_buffer: list[dict] = []
        self._distillation_buffer: list[dict] = []
        self._schemas: dict[str, dict] = {}
        self._instance_counter: int = 0

        self.create_subscription(String, "/grace/dreaming/distillation",
                                 self._on_distillation, 10)
        self.create_subscription(String, "/grace/subconscious/episodic",
                                 self._on_episodic, 10)
        self.create_subscription(String, "/grace/subconscious/semantic",
                                 self._on_semantic, 10)

        self._pub = self.create_publisher(String, "/grace/dreaming/schema_state", 10)
        self.create_timer(1.0 / hz, self._process)
        self.get_logger().info("SchemaFormation ready.")

    def _on_distillation(self, msg: String):
        try:
            self._distillation_buffer.append(json.loads(msg.data))
            if len(self._distillation_buffer) > 20:
                self._distillation_buffer.pop(0)
        except Exception:
            pass

    def _on_episodic(self, msg: String):
        try:
            self._episodic_buffer.append(json.loads(msg.data))
            if len(self._episodic_buffer) > 100:
                self._episodic_buffer.pop(0)
        except Exception:
            pass

    def _on_semantic(self, msg: String):
        try:
            self._semantic_buffer.append(json.loads(msg.data))
            if len(self._semantic_buffer) > 100:
                self._semantic_buffer.pop(0)
        except Exception:
            pass

    def _extract_tags(self, entry: dict) -> list[str]:
        return entry.get("tags", []) if isinstance(entry.get("tags"), list) else []

    def _cluster_key(self, tags: list[str]) -> str:
        if not tags:
            return "general"
        return "_".join(sorted(tags[:3]))

    def _process(self):
        now = time.time()
        instances = []

        for e in self._episodic_buffer[-10:]:
            tags = self._extract_tags(e)
            content = e.get("content", "")[:80]
            emotional_tag = e.get("emotional_tag", 0.0)
            instances.append((tags, content, emotional_tag, "episodic"))

        for s in self._semantic_buffer[-5:]:
            tags = self._extract_tags(s)
            content = s.get("content", "")[:80]
            confidence = s.get("confidence", 0.5)
            instances.append((tags, content, confidence, "semantic"))

        for d in self._distillation_buffer:
            for insight in d.get("insights", []):
                instances.append(([], f"insight:{insight}", 0.5, "insight"))

        for tags, content, val, source in instances:
            key = self._cluster_key(tags)
            if key not in self._schemas:
                schema_id = hashlib.md5(key.encode()).hexdigest()[:8]
                self._schemas[key] = {
                    "schema_id": schema_id,
                    "schema_content": key,
                    "instances": [],
                    "abstraction_level": 0.2,
                    "predictive_power": 0.3,
                    "flexibility": 0.3,
                }

            schema = self._schemas[key]
            schema["instances"].append({"content": content, "source": source,
                                        "value": val, "timestamp": now})
            if len(schema["instances"]) > 20:
                schema["instances"].pop(0)

            n = len(schema["instances"])
            schema["abstraction_level"] = min(1.0, 0.2 + n * 0.04)
            schema["predictive_power"] = min(1.0, 0.3 + n * 0.03)
            diverse_tags = len(set(t for tags, _, _, _ in
                                   schema["instances"] for t in tags))
            schema["flexibility"] = min(1.0, 0.3 + diverse_tags * 0.05)

            self._instance_counter += 1

        if not self._schemas:
            return

        active_key = max(self._schemas, key=lambda k: self._schemas[k]["instances"])
        schema = self._schemas[active_key]

        state = SchemaState(
            schema_id=schema["schema_id"],
            schema_content=schema["schema_content"],
            abstraction_level=schema["abstraction_level"],
            instances_encoded=len(schema["instances"]),
            predictive_power=schema["predictive_power"],
            flexibility=schema["flexibility"],
        )
        out = String(); out.data = to_json(state)
        self._pub.publish(out)

        if self._instance_counter % 50 == 0:
            self.get_logger().info(
                f"Schema '{active_key}': {len(schema['instances'])} instances, "
                f"abstraction {schema['abstraction_level']:.2f}")


def main(args=None):
    rclpy.init(args=args)
    node = SchemaFormationNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
