"""
grace_agi/qualia/temporal_qualia.py
Non-SLM node — Temporal Qualia.
Models the subjective experience of time passage (felt duration, time pressure,
temporal coherence). Influenced by circadian rhythm, arousal, and conscious
content complexity.
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String

from grace.utils.schemas import TemporalQualiaState, to_json


class TemporalQualiaNode(Node):
    def __init__(self):
        super().__init__("grace_temporal_qualia")

        self.declare_parameter("update_hz", 1.0)
        hz = self.get_parameter("update_hz").value

        self._circadian = {}
        self._affect = {}
        self._gw = {}

        self._state = TemporalQualiaState()
        self._last_update = time.time()

        self.create_subscription(String, "/grace/vital/circadian_rhythm",
                                 lambda m: self._set(m, "_circadian"), 10)
        self.create_subscription(String, "/grace/unconscious/affective_state",
                                 lambda m: self._set(m, "_affect"), 10)
        self.create_subscription(String, "/grace/conscious/global_workspace",
                                 lambda m: self._set(m, "_gw"), 10)

        self._pub = self.create_publisher(String, "/grace/qualia/temporal", 10)
        self.create_timer(1.0 / hz, self._update)
        self.get_logger().info("TemporalQualia ready.")

    def _set(self, msg, attr):
        try:
            setattr(self, attr, json.loads(msg.data))
        except Exception:
            pass

    def _update(self):
        now = time.time()
        dt = now - self._last_update
        self._last_update = now

        arousal = self._affect.get("arousal", 0.3)
        valence = self._affect.get("valence", 0.5)
        phase = self._circadian.get("circadian_phase", 0.0)
        energy = self._circadian.get("energy", 0.6)
        broadcast = self._gw.get("broadcast", "")

        content_length = len(broadcast)

        self._state.time_pressure = max(0.0, min(1.0,
            self._state.time_pressure + (arousal - 0.5) * 0.1))
        self._state.time_pressure = max(0.0, self._state.time_pressure * 0.98)

        self._state.felt_duration = max(0.5, min(2.0,
            1.0 + (arousal - 0.5) * 0.5 + (1.0 - energy) * 0.3))
        self._state.felt_duration += (0.5 - self._state.felt_duration) * 0.05

        self._state.temporal_coherence = max(0.0, min(1.0,
            0.7 - self._state.time_pressure * 0.3 + (0.5 - abs(arousal - 0.5)) * 0.2))

        self._state.present_moment_awareness = max(0.0, min(1.0,
            0.5 + (valence - 0.5) * 0.3 - self._state.time_pressure * 0.2))

        self._state.temporal_depth = max(0.0, min(1.0,
            0.3 + phase * 0.4 + energy * 0.2 + (1.0 - arousal) * 0.1))

        out = String()
        out.data = to_json(self._state)
        self._pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = TemporalQualiaNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
