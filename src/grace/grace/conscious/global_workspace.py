"""
grace_agi/conscious/global_workspace.py
The Global Neuronal Workspace — aggregates all incoming conscious broadcasts,
selects the highest-salience item, and re-broadcasts to all consumers.
Implements late ignition: only content above the ignition threshold fires.
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.grace.utils.schemas import GlobalWorkspaceContent, to_json

IGNITION_THRESHOLD = 0.3    # min salience to broadcast
BROADCAST_HZ       = 2.0


class GlobalWorkspaceNode(Node):
    def __init__(self):
        super().__init__("grace_global_workspace")

        self._candidates: list[dict] = []   # buffered incoming content

        # All sources that feed the workspace
        input_topics = [
            "/grace/unconscious/thalamic_broadcast",
            "/grace/unconscious/relevance",
            "/grace/conscious/memory_context",
            "/grace/conscious/salience",
            "/grace/conscious/dmn",
            "/grace/qualia/field",
        ]
        for topic in input_topics:
            self.create_subscription(String, topic, self._on_input, 10)

        # Self-feedback from downstream
        self.create_subscription(String, "/grace/conscious/metacognition",
                                 self._on_meta, 10)

        self._pub = self.create_publisher(String, "/grace/conscious/global_workspace", 10)
        self.create_timer(1.0 / BROADCAST_HZ, self._broadcast)
        self.get_logger().info("GlobalWorkspace ready.")

    def _on_input(self, msg: String):
        try:
            d = json.loads(msg.data)
            # Accept items that look like GlobalWorkspaceContent or have a salience field
            content  = (d.get("broadcast") or d.get("content") or
                        d.get("phenomenal_content") or d.get("inner_monologue", ""))
            salience = d.get("salience", d.get("score", 0.4))
            if content:
                self._candidates.append({
                    "broadcast": str(content)[:200],
                    "salience":  float(salience),
                    "sources":   d.get("sources", ["unknown"]),
                    "timestamp": d.get("timestamp", time.time()),
                })
        except Exception: pass

    def _on_meta(self, msg: String):
        try:
            d = json.loads(msg.data)
            if d.get("redirect_to_executive"):
                self._candidates.append({
                    "broadcast": "Metacognition requests re-evaluation",
                    "salience":  0.7,
                    "sources":   ["metacognition"],
                    "timestamp": time.time(),
                })
        except Exception: pass

    def _broadcast(self):
        if not self._candidates:
            return

        # Late ignition: pick highest-salience item above threshold
        above = [c for c in self._candidates if c["salience"] >= IGNITION_THRESHOLD]
        if not above:
            self._candidates.clear()
            return

        winner = max(above, key=lambda c: c["salience"])
        self._candidates.clear()

        gw = GlobalWorkspaceContent(
            broadcast=winner["broadcast"],
            sources=winner.get("sources", []),
            salience=winner["salience"],
        )
        out = String(); out.data = to_json(gw)
        self._pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = GlobalWorkspaceNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
