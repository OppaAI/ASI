"""
grace_agi/qualia/phenomenal_binding.py
Non-SLM node — Phenomenal Binding.
Binds together multiple qualia streams (field, bodily, temporal, self-subject)
into a unified phenomenal experience. Tracks coherence, modality integration,
and unity quality.
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String

from grace.utils.schemas import PhenomenalBindingState, to_json


class PhenomenalBindingNode(Node):
    def __init__(self):
        super().__init__("grace_phenomenal_binding")

        self.declare_parameter("update_hz", 2.0)
        hz = self.get_parameter("update_hz").value

        self._field: dict = {}
        self._bodily: dict = {}
        self._temporal: dict = {}
        self._self_subject: dict = {}
        self._last_field_time: float = 0.0
        self._last_bodily_time: float = 0.0
        self._last_temporal_time: float = 0.0
        self._last_self_time: float = 0.0
        self._stale_threshold: float = 5.0

        self.create_subscription(String, "/grace/qualia/field",
                                 self._on_field, 10)
        self.create_subscription(String, "/grace/qualia/bodily",
                                 self._on_bodily, 10)
        self.create_subscription(String, "/grace/qualia/temporal",
                                 self._on_temporal, 10)
        self.create_subscription(String, "/grace/qualia/self_subject",
                                 self._on_self_subject, 10)

        self._pub = self.create_publisher(String, "/grace/qualia/phenomenal_binding", 10)
        self.create_timer(1.0 / hz, self._process)
        self.get_logger().info("PhenomenalBinding ready.")

    def _on_field(self, msg: String):
        try:
            self._field = json.loads(msg.data)
            self._last_field_time = time.time()
        except Exception:
            pass

    def _on_bodily(self, msg: String):
        try:
            self._bodily = json.loads(msg.data)
            self._last_bodily_time = time.time()
        except Exception:
            pass

    def _on_temporal(self, msg: String):
        try:
            self._temporal = json.loads(msg.data)
            self._last_temporal_time = time.time()
        except Exception:
            pass

    def _on_self_subject(self, msg: String):
        try:
            self._self_subject = json.loads(msg.data)
            self._last_self_time = time.time()
        except Exception:
            pass

    def _is_stale(self, last_time: float) -> bool:
        return (time.time() - last_time) > self._stale_threshold

    def _process(self):
        now = time.time()

        streams = {
            "field": (self._field, self._last_field_time, "phenomenal_field"),
            "bodily": (self._bodily, self._last_bodily_time, "bodily_qualia"),
            "temporal": (self._temporal, self._last_temporal_time, "temporal_qualia"),
            "self_subject": (self._self_subject, self._last_self_time, "self_subject_qualia"),
        }

        active_modalities = []
        fresh_count = 0
        for name, (data, last_time, label) in streams.items():
            if data and not self._is_stale(last_time):
                fresh_count += 1
                active_modalities.append(label)

        total_possible = len(streams)
        binding_active = fresh_count >= 2

        if fresh_count == 0:
            coherence = 0.0
            modality_integration = 0.0
            unity = 0.0
        else:
            field_unity = self._field.get("unity_score", 0.0) if self._field else 0.0
            bodily_tension = self._bodily.get("body_tension", 0.3) if self._bodily else 0.3
            temporal_coherence = self._temporal.get("temporal_coherence", 0.5) if self._temporal else 0.5
            mineness = self._self_subject.get("mineness", 0.5) if self._self_subject else 0.5
            ipseity = self._self_subject.get("ipseity", 0.5) if self._self_subject else 0.5

            relaxed = 1.0 - bodily_tension
            coherence = (field_unity * 0.3 + temporal_coherence * 0.25 +
                         mineness * 0.25 + relaxed * 0.2)
            coherence = min(1.0, coherence)

            modality_integration = fresh_count / total_possible
            cross_modality = 1.0 - abs(field_unity - temporal_coherence) * 0.5
            modality_integration = (modality_integration * 0.6 + cross_modality * 0.4)

            unity = (coherence * 0.4 + modality_integration * 0.3 +
                     ipseity * 0.3)
            unity = min(1.0, unity)

        if fresh_count < 2:
            coherence *= 0.5
            modality_integration *= 0.5
            unity *= 0.5

        state = PhenomenalBindingState(
            binding_active=binding_active,
            bound_elements=active_modalities,
            binding_coherence=round(coherence, 3),
            modality_integration=round(modality_integration, 3),
            unity_quality=round(unity, 3),
        )
        out = String(); out.data = to_json(state)
        self._pub.publish(out)

        if int(now) % 10 == 0:
            self.get_logger().info(
                f"PhenomenalBinding: {fresh_count}/{total_possible} streams, "
                f"coherence={coherence:.2f}, unity={unity:.2f}, "
                f"active={active_modalities}")


def main(args=None):
    rclpy.init(args=args)
    node = PhenomenalBindingNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
