"""
grace_agi/dreaming/memory_reconsolidation.py
Non-SLM node — Memory Reconsolidation.
Models retrieval-induced modification of memories: destabilization followed
by re-stabilization with emotional reappraisal.
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String

from grace.utils.schemas import MemoryReconsolidationState, to_json


class MemoryReconsolidationNode(Node):
    def __init__(self):
        super().__init__("grace_memory_reconsolidation")

        self.declare_parameter("update_hz", 10.0)
        hz = self.get_parameter("update_hz").value

        self._episodic_buffer: list[dict] = []
        self._semantic_buffer: list[dict] = []
        self._consolidation_trigger: dict = {}
        self._active_memory: dict | None = None
        self._destabilization: float = 0.0
        self._reappraisal: float = 0.0
        self._reconsolidating: bool = False
        self._cycle: int = 0

        self.create_subscription(String, "/grace/dreaming/consolidation",
                                 self._on_consolidation, 10)
        self.create_subscription(String, "/grace/subconscious/episodic",
                                 self._on_episodic, 10)
        self.create_subscription(String, "/grace/subconscious/semantic",
                                 self._on_semantic, 10)

        self._pub = self.create_publisher(String, "/grace/dreaming/reconsolidation", 10)
        self.create_timer(1.0 / hz, self._process)
        self.get_logger().info("MemoryReconsolidation ready.")

    def _on_consolidation(self, msg: String):
        try:
            self._consolidation_trigger = json.loads(msg.data)
        except Exception:
            pass

    def _on_episodic(self, msg: String):
        try:
            self._episodic_buffer.append(json.loads(msg.data))
            if len(self._episodic_buffer) > 50:
                self._episodic_buffer.pop(0)
        except Exception:
            pass

    def _on_semantic(self, msg: String):
        try:
            self._semantic_buffer.append(json.loads(msg.data))
            if len(self._semantic_buffer) > 50:
                self._semantic_buffer.pop(0)
        except Exception:
            pass

    def _process(self):
        self._cycle += 1

        if not self._reconsolidating:
            triggers = self._consolidation_trigger.get("new_episodic", [])
            if triggers and self._episodic_buffer:
                memory = self._episodic_buffer[-1]
                self._active_memory = memory
                self._destabilization = min(1.0, len(triggers) * 0.15 + 0.2)
                self._reappraisal = 0.0
                self._reconsolidating = True
                self.get_logger().debug(f"Destabilizing memory: {memory.get('content','')[:40]}")
                self._consolidation_trigger = {}
            return

        self._destabilization = max(0.0, self._destabilization - 0.05)
        if self._destabilization > 0.2:
            emotional_tag = self._active_memory.get("emotional_tag", 0.0)
            tag_shift = (0.5 - emotional_tag) * 0.02
            self._reappraisal = min(1.0, self._reappraisal + abs(tag_shift))
        else:
            self._reappraisal = min(1.0, self._reappraisal + 0.03)

        if self._destabilization <= 0.05 or self._reappraisal >= 0.8:
            self._reconsolidating = False
            old_tag = self._active_memory.get("emotional_tag", 0.0)
            new_tag = old_tag + (0.5 - old_tag) * self._reappraisal * 0.3

            state = MemoryReconsolidationState(
                reconsolidation_active=False,
                memory_id=str(self._active_memory.get("timestamp", time.time())),
                modification_applied=(
                    f"emotional_reappraisal:{old_tag:.2f}->{new_tag:.2f}"),
                emotional_reappraisal=self._reappraisal,
                destabilization_level=self._destabilization,
                re_stabilized=True,
            )
            out = String(); out.data = to_json(state)
            self._pub.publish(out)
            self.get_logger().info(
                f"Reconsolidated: tag {old_tag:.2f} -> {new_tag:.2f}")
            self._active_memory = None
            self._destabilization = 0.0
            self._reappraisal = 0.0


def main(args=None):
    rclpy.init(args=args)
    node = MemoryReconsolidationNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
