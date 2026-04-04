"""
grace_agi/conscious/memory_coordinator.py
Cross-layer memory integration — pulls from episodic, semantic,
procedural, social recall and assembles a unified context for the
Global Workspace.
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.utils.schemas import GlobalWorkspaceContent, to_json


class MemoryCoordinatorNode(Node):
    def __init__(self):
        super().__init__("grace_memory_coordinator")

        self._episodic   = []
        self._semantic   = []
        self._procedural = []
        self._social     = {}
        self._wm         = {}

        for topic, attr in [
            ("/grace/subconscious/episodic_recall",   "_episodic"),
            ("/grace/subconscious/semantic_recall",   "_semantic"),
            ("/grace/subconscious/procedural_recall", "_procedural"),
            ("/grace/subconscious/social_recall",     "_social"),
            ("/grace/conscious/working_memory",       "_wm"),
        ]:
            self.create_subscription(
                String, topic,
                lambda m, a=attr: self._store(m, a), 10)

        self._pub = self.create_publisher(String, "/grace/conscious/memory_context", 10)
        self.create_timer(1.5, self._integrate)
        self.get_logger().info("MemoryCoordinator ready.")

    def _store(self, msg, attr):
        try:
            d = json.loads(msg.data)
            setattr(self, attr, d)
        except Exception: pass

    def _integrate(self):
        active = self._wm.get("active_thought", "")
        context_parts = []

        if self._episodic:
            recalled = self._episodic.get("recalled", [])[:2]
            if recalled:
                context_parts.append(f"Episodic: {recalled[0].get('content','')[:80]}")

        if self._semantic:
            recalled = self._semantic.get("recalled", [])[:2]
            if recalled:
                context_parts.append(f"Semantic: {recalled[0].get('content','')[:80]}")

        if self._procedural:
            skills = self._procedural.get("skills", [])[:2]
            if skills:
                context_parts.append(
                    f"Skills: {', '.join(s.get('skill','') for s in skills)}")

        if self._social and isinstance(self._social, dict):
            gd = self._social.get("group_dynamic", "")
            if gd:
                context_parts.append(f"Social: {gd}")

        if not context_parts:
            return

        broadcast = f"[{active[:40]}] " + " | ".join(context_parts)
        gw = GlobalWorkspaceContent(
            broadcast=broadcast,
            sources=["memory_coordinator"],
            salience=0.6,
        )
        out = String(); out.data = to_json(gw)
        self._pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(MemoryCoordinatorNode())
    rclpy.shutdown()
