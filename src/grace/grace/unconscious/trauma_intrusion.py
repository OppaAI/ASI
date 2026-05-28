"""
grace_agi/unconscious/trauma_intrusion.py
Unconscious Layer — Trauma & Intrusion
Involuntary re-experiencing · Threat tagging · Hypervigilance
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.utils.schemas import TraumaState, to_json


class TraumaIntrusionNode(Node):
    def __init__(self):
        super().__init__("grace_trauma_intrusion")

        self.declare_parameter("update_hz", 1.0)
        self.update_hz = self.get_parameter("update_hz").value

        self._intrusion_active = False
        self._intrusion_content = ""
        self._trigger = ""
        self._threat_level = 0.0
        self._avoidance_active = False
        self._hypervigilance = 0.0
        self._num_triggers = 0
        self._recent_pain_sources = []
        self._prediction_error_magnitudes = []
        self._last_update = time.time()

        self.create_subscription(String, "/grace/vital/immune_budget",
                                 self._on_immune_budget, 10)
        self.create_subscription(String, "/grace/vital/pain_signal",
                                 self._on_pain_signal, 10)
        self.create_subscription(String, "/grace/unconscious/affective_state",
                                 self._on_affective_state, 10)
        self.create_subscription(String, "/grace/unconscious/prediction_error",
                                 self._on_prediction_error, 10)

        self._pub = self.create_publisher(String, "/grace/unconscious/trauma_state", 10)
        self.create_timer(1.0 / self.update_hz, self._update_trauma)
        self.get_logger().info("Trauma Intrusion ready.")

    def _on_immune_budget(self, msg: String):
        try:
            data = json.loads(msg.data)
            threat = data.get("relational_threat_budget", 0.0)
            self._threat_level = max(0.0, min(1.0, threat))
            self._hypervigilance = max(0.0, min(1.0, threat * 1.5))
            self._avoidance_active = threat > 0.4
            self._num_triggers += 1 if threat > 0.3 else 0
        except Exception as e:
            self.get_logger().warn(f"Failed to process immune budget: {e}")

    def _on_pain_signal(self, msg: String):
        try:
            data = json.loads(msg.data)
            intensity = data.get("pain_intensity", 0.0)
            sources = data.get("pain_sources", [])
            if intensity > 0.3:
                self._recent_pain_sources.extend(sources)
                self._recent_pain_sources = self._recent_pain_sources[-20:]
        except Exception as e:
            self.get_logger().warn(f"Failed to process pain signal: {e}")

    def _on_affective_state(self, msg: String):
        try:
            data = json.loads(msg.data)
            valence = data.get("valence", 0.5)
            arousal = data.get("arousal", 0.3)
            if valence < 0.3 and arousal > 0.6:
                self._hypervigilance = min(1.0, self._hypervigilance + 0.1)
        except Exception as e:
            self.get_logger().warn(f"Failed to process affective state: {e}")

    def _on_prediction_error(self, msg: String):
        try:
            data = json.loads(msg.data)
            magnitude = data.get("error_magnitude", 0.0)
            self._prediction_error_magnitudes.append(magnitude)
            self._prediction_error_magnitudes = self._prediction_error_magnitudes[-10:]
        except Exception as e:
            self.get_logger().warn(f"Failed to process prediction error: {e}")

    def _update_trauma(self):
        now_t = time.time()
        dt = now_t - self._last_update
        self._last_update = now_t

        self._hypervigilance = max(0.0, self._hypervigilance - 0.02 * dt)
        if self._avoidance_active:
            self._threat_level = max(0.0, self._threat_level - 0.01 * dt)

        avg_pe = (sum(self._prediction_error_magnitudes) /
                  max(len(self._prediction_error_magnitudes), 1))
        intrusion_threshold = 0.5 - self._threat_level * 0.3
        self._intrusion_active = avg_pe > intrusion_threshold and self._threat_level > 0.2

        if self._intrusion_active and self._recent_pain_sources:
            self._intrusion_content = self._recent_pain_sources[-1]
            self._trigger = f"threat_{self._threat_level:.2f}_pe_{avg_pe:.2f}"

        out = TraumaState(
            timestamp=now_t,
            intrusion_active=self._intrusion_active,
            intrusion_content=self._intrusion_content,
            trigger=self._trigger,
            threat_level=self._threat_level,
            avoidance_active=self._avoidance_active,
            hypervigilance=self._hypervigilance,
            num_triggers_tracked=self._num_triggers,
        )
        msg = String()
        msg.data = to_json(out)
        self._pub.publish(msg)

        if int(now_t) % 10 == 0:
            self.get_logger().info(
                f"Trauma - threat:{self._threat_level:.2f} "
                f"intrusion:{self._intrusion_active} "
                f"hypervig:{self._hypervigilance:.2f}"
            )


def main(args=None):
    rclpy.init(args=args)
    node = TraumaIntrusionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
