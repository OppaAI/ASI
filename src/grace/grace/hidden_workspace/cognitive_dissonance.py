"""
grace_agi/hidden_workspace/cognitive_dissonance.py
Hidden Workspace — Cognitive Dissonance Detector
Rule-based detection of dissonance between conflicting beliefs/attitudes.
"""
import json
import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.utils.schemas import CognitiveDissonanceState, to_json
from math import exp


RESOLUTION_STRATEGIES = [
    "change_belief", "add_consonant_cognition",
    "trivialize", "deny", "shift_importance",
]


class CognitiveDissonanceNode(Node):
    def __init__(self):
        super().__init__("grace_cognitive_dissonance")

        self.declare_parameter("update_hz", 0.5)
        self.update_hz = self.get_parameter("update_hz").value

        self._dissonance_level = 0.0
        self._conflicting_beliefs = []
        self._resolution_attempted = False
        self._resolution_strategy = ""
        self._motivated_reasoning = False
        self._arousal = 0.0
        self._last_narrative_coherence = 0.7
        self._last_update = time.time()

        self.create_subscription(String, "/grace/subconscious/attitudes",
                                 self._on_attitudes, 10)
        self.create_subscription(String, "/grace/conscience/verdict",
                                 self._on_verdict, 10)
        self.create_subscription(String, "/grace/hidden/narrative_coherence",
                                 self._on_narrative, 10)

        self._pub = self.create_publisher(String, "/grace/hidden/cognitive_dissonance", 10)
        self.create_timer(1.0 / self.update_hz, self._tick)
        self.get_logger().info("Cognitive Dissonance ready.")

    def _on_attitudes(self, msg: String):
        try:
            d = json.loads(msg.data)
            evals = d.get("evaluations", {})
            dissonance = d.get("dissonance_level", 0.0)
            if dissonance > 0.1:
                self._dissonance_level = dissonance
                self._conflicting_beliefs = [
                    f"{k}:{v}" for k, v in evals.items()
                    if isinstance(v, (int, float)) and abs(v) < 0.3
                ]
        except Exception:
            pass

    def _on_verdict(self, msg: String):
        try:
            d = json.loads(msg.data)
            verdict = d.get("verdict", "neutral")
            if verdict in ("immoral", "uncertain"):
                self._dissonance_level = min(1.0, self._dissonance_level + 0.15)
                self._conflicting_beliefs.append(f"verdict:{verdict}")
        except Exception:
            pass

    def _on_narrative(self, msg: String):
        try:
            d = json.loads(msg.data)
            self._last_narrative_coherence = d.get("coherence_score", 0.7)
            if d.get("gaps_detected", 0) > 1:
                self._dissonance_level = min(1.0, self._dissonance_level + 0.08)
        except Exception:
            pass

    def _tick(self):
        now = time.time()
        dt = now - self._last_update
        self._last_update = now

        if self._dissonance_level > 0.4 and not self._resolution_attempted:
            self._resolution_attempted = True
            self._resolution_strategy = RESOLUTION_STRATEGIES[
                int(now) % len(RESOLUTION_STRATEGIES)
            ]
            self._motivated_reasoning = self._dissonance_level > 0.6

        if self._resolution_attempted:
            resolve_rate = 0.03 * dt
            self._dissonance_level = max(0.0, self._dissonance_level - resolve_rate)
            self._arousal = max(0.0, self._arousal - resolve_rate * 2)

            if self._dissonance_level < 0.2:
                self._resolution_attempted = False
                self._resolution_strategy = ""
                self._motivated_reasoning = False
        else:
            decay = exp(-0.02 * dt)
            self._dissonance_level = max(0.0, self._dissonance_level * decay)
            self._arousal = max(0.0, self._arousal * decay)

        self._arousal = min(1.0, self._dissonance_level * 0.7 + 0.1)
        unique_beliefs = list(set(self._conflicting_beliefs[-15:]))

        state = CognitiveDissonanceState(
            timestamp=now,
            dissonance_level=round(self._dissonance_level, 3),
            conflicting_beliefs=unique_beliefs,
            resolution_attempted=self._resolution_attempted,
            resolution_strategy=self._resolution_strategy,
            motivated_reasoning_active=self._motivated_reasoning,
            arousal=round(self._arousal, 3),
        )
        out = String()
        out.data = to_json(state)
        self._pub.publish(out)

        if self._dissonance_level > 0.6 and int(now) % 6 == 0:
            self.get_logger().warn(
                f"Dissonance: {self._dissonance_level:.2f} "
                f"strategy={self._resolution_strategy} "
                f"motivated={self._motivated_reasoning}"
            )


def main(args=None):
    rclpy.init(args=args)
    node = CognitiveDissonanceNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
