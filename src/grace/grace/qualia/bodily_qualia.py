"""
grace_agi/qualia/bodily_qualia.py
Non-SLM node — Bodily Qualia.
Generates the felt sense of the body from sensor data, pain signals, metabolic
resources, and affective state. Tracks fatigue, tension, and somatic markers.
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String

from grace.utils.schemas import BodilyQualiaState, to_json


class BodilyQualiaNode(Node):
    def __init__(self):
        super().__init__("grace_bodily_qualia")

        self.declare_parameter("update_hz", 0.5)
        hz = self.get_parameter("update_hz").value

        self._sensors = {}
        self._pain = {}
        self._metabolic = {}
        self._affect = {}

        self.create_subscription(String, "/grace/sensors/bundle",
                                 lambda m: self._set(m, "_sensors"), 10)
        self.create_subscription(String, "/grace/vital/pain_signal",
                                 lambda m: self._set(m, "_pain"), 10)
        self.create_subscription(String, "/grace/vital/metabolic_resource",
                                 lambda m: self._set(m, "_metabolic"), 10)
        self.create_subscription(String, "/grace/unconscious/affective_state",
                                 lambda m: self._set(m, "_affect"), 10)

        self._pub = self.create_publisher(String, "/grace/qualia/bodily", 10)
        self.create_timer(1.0 / hz, self._update)
        self.get_logger().info("BodilyQualia ready.")

    def _set(self, msg, attr):
        try:
            setattr(self, attr, json.loads(msg.data))
        except Exception:
            pass

    def _update(self):
        state = BodilyQualiaState()

        pain_intensity = self._pain.get("pain_intensity", 0.0)
        pain_sources = self._pain.get("pain_sources", [])
        glucose = self._metabolic.get("glucose_equivalent", 1.0)
        effective = self._metabolic.get("effective_glucose", 1.0)
        valence = self._affect.get("valence", 0.5)
        arousal = self._affect.get("arousal", 0.3)

        state.fatigue_level = max(0.0, 1.0 - effective)
        state.body_tension = min(1.0, pain_intensity * 0.7 + arousal * 0.3)
        state.interoceptive_awareness = 0.3 + arousal * 0.4

        state.somatic_markers = list(pain_sources)
        if glucose < 0.3:
            state.somatic_markers.append("fatigue")
        if pain_intensity > 0.5:
            state.somatic_markers.append("discomfort")
        if arousal > 0.7:
            state.somatic_markers.append("tremor")
        if valence < 0.3:
            state.somatic_markers.append("heaviness")

        if state.fatigue_level > 0.7:
            felt = "exhausted"
        elif state.fatigue_level > 0.4:
            felt = "weary"
        elif state.body_tension > 0.6:
            felt = "tense"
        elif valence > 0.6 and arousal < 0.4:
            felt = "relaxed"
        elif arousal > 0.6:
            felt = "energized"
        else:
            felt = "neutral"

        state.felt_sense = felt

        out = String()
        out.data = to_json(state)
        self._pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = BodilyQualiaNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
