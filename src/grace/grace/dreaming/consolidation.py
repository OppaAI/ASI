"""
grace_agi/dreaming/consolidation.py
Consolidation Across Layers — the slow-learning mechanism.
Receives distilled insights and broadcasts a ConsolidationPacket
to every persistent subsystem: episodic, semantic, procedural,
affective, personality, values, social, workspace, self-model,
DMN, and conscience.
Also receives conscience reflections for moral consolidation.
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String

from grace.grace.utils.schemas import ConsolidationPacket, to_json


class ConsolidationNode(Node):
    def __init__(self):
        super().__init__("grace_consolidation")

        self._distillation_buffer: list[dict] = []
        self._conscience_buffer:   list[dict] = []

        self.create_subscription(String, "/grace/dreaming/distillation",
                                 self._on_distillation, 10)
        self.create_subscription(String, "/grace/conscience/verdict",
                                 self._on_conscience,   10)

        # Single broadcast topic — all persistent nodes subscribe to this
        self._pub = self.create_publisher(String, "/grace/dreaming/consolidation", 10)

        # Consolidate every 60 seconds (accumulate a batch first)
        self.create_timer(60.0, self._consolidate)
        self.get_logger().info("Consolidation ready.")

    def _on_distillation(self, msg: String):
        try:
            self._distillation_buffer.append(json.loads(msg.data))
        except Exception: pass

    def _on_conscience(self, msg: String):
        try:
            v = json.loads(msg.data)
            if v.get("verdict") in ("moral", "immoral"):
                self._conscience_buffer.append(v)
        except Exception: pass

    def _consolidate(self):
        if not self._distillation_buffer and not self._conscience_buffer:
            return

        self.get_logger().info(
            f"Consolidation: merging {len(self._distillation_buffer)} distillation "
            f"+ {len(self._conscience_buffer)} conscience packets.")

        # ── Merge all distillation packets ────────────────────────────────────
        merged_insights:    list[str]  = []
        merged_personality: dict       = {}
        merged_values:      dict       = {}
        merged_episodic:    list[dict] = []
        merged_semantic:    list[dict] = []

        for pkt in self._distillation_buffer:
            merged_insights.extend(pkt.get("insights", []))

            for k, v in pkt.get("personality_deltas", {}).items():
                merged_personality[k] = merged_personality.get(k, 0.0) + v

            for k, v in pkt.get("value_updates", {}).items():
                merged_values[k] = v   # last-write wins for values

            merged_episodic.extend(pkt.get("new_episodic", []))
            merged_semantic.extend(pkt.get("new_semantic", []))

        # ── Absorb conscience reflections as semantic memories ────────────────
        for v in self._conscience_buffer:
            merged_semantic.append({
                "content":    (f"Moral lesson: situation '{v.get('situation','')[:60]}' "
                               f"was judged {v.get('verdict')} — {v.get('reasoning','')[:80]}"),
                "confidence": v.get("confidence", 0.7),
                "tags":       ["conscience", "moral", v.get("verdict", "neutral")],
                "timestamp":  v.get("timestamp", time.time()),
            })

        # ── Build and broadcast ConsolidationPacket ───────────────────────────
        packet = ConsolidationPacket(
            insights=merged_insights[:20],          # cap to avoid flooding
            personality_deltas=merged_personality,
            value_updates=merged_values,
            new_episodic=merged_episodic[:10],
            new_semantic=merged_semantic[:10],
        )

        out = String(); out.data = to_json(packet)
        self._pub.publish(out)

        self.get_logger().info(
            f"Consolidation: broadcast — {len(merged_insights)} insights, "
            f"{len(merged_episodic)} episodic, {len(merged_semantic)} semantic entries.")

        # Clear buffers after consolidation
        self._distillation_buffer.clear()
        self._conscience_buffer.clear()


def main(args=None):
    rclpy.init(args=args)
    node = ConsolidationNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
