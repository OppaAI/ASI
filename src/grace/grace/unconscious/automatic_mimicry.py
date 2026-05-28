"""
grace_agi/unconscious/automatic_mimicry.py
Unconscious Layer — Automatic Mimicry
Behavioral synchrony · Unconscious mirroring · Resonance tracking
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.utils.schemas import MimicryState, to_json


class AutomaticMimicryNode(Node):
    def __init__(self):
        super().__init__("grace_automatic_mimicry")

        self.declare_parameter("update_hz", 2.0)
        self.update_hz = self.get_parameter("update_hz").value
        self.declare_parameter("mimicry_threshold", 0.3)
        self._mimicry_threshold = self.get_parameter("mimicry_threshold").value

        self._mimicry_active = False
        self._mirrored_behavior = ""
        self._synchrony_level = 0.0
        self._resonance_intensity = 0.0
        self._target_agent = ""
        self._automatic = True
        self._social_presence = 0.0
        self._last_update = time.time()

        self.create_subscription(String, "/grace/sensors/bundle",
                                 self._on_sensor_bundle, 10)
        self.create_subscription(String, "/grace/subconscious/social_model",
                                 self._on_social_model, 10)

        self._pub = self.create_publisher(String, "/grace/unconscious/mimicry_state", 10)
        self.create_timer(1.0 / self.update_hz, self._update_mimicry)
        self.get_logger().info("Automatic Mimicry ready.")

    def _on_sensor_bundle(self, msg: String):
        try:
            data = json.loads(msg.data)
            social_cues = data.get("social_cues", "")
            if social_cues:
                self._social_presence = 0.5 if "person" in social_cues.lower() else 0.1
                if "friendly" in social_cues.lower():
                    self._resonance_intensity = min(1.0, self._resonance_intensity + 0.2)
                elif "hostile" in social_cues.lower():
                    self._resonance_intensity = max(0.0, self._resonance_intensity - 0.1)
        except Exception as e:
            self.get_logger().warn(f"Failed to process sensor bundle: {e}")

    def _on_social_model(self, msg: String):
        try:
            data = json.loads(msg.data)
            agents = data.get("agents_detected", [])
            empathy = data.get("empathy_level", 0.5)
            if agents:
                self._target_agent = agents[0].get("id", "unknown") if isinstance(agents[0], dict) else str(agents[0])
            self._resonance_intensity = max(0.0, min(1.0,
                self._resonance_intensity + empathy * 0.1))
        except Exception as e:
            self.get_logger().warn(f"Failed to process social model: {e}")

    def _update_mimicry(self):
        now_t = time.time()
        dt = now_t - self._last_update
        self._last_update = now_t

        self._resonance_intensity = max(0.0, self._resonance_intensity - 0.05 * dt)

        self._synchrony_level = self._social_presence * self._resonance_intensity
        self._synchrony_level = max(0.0, min(1.0, self._synchrony_level))

        self._mimicry_active = self._synchrony_level > self._mimicry_threshold

        if self._mimicry_active:
            if self._synchrony_level > 0.7:
                self._mirrored_behavior = "full_mirroring"
            elif self._synchrony_level > 0.5:
                self._mirrored_behavior = "posture_echo"
            else:
                self._mirrored_behavior = "subtle_synchrony"
        else:
            self._mirrored_behavior = ""

        out = MimicryState(
            timestamp=now_t,
            mimicry_active=self._mimicry_active,
            mirrored_behavior=self._mirrored_behavior,
            synchrony_level=self._synchrony_level,
            resonance_intensity=self._resonance_intensity,
            target_agent=self._target_agent,
            automatic=self._automatic,
        )
        msg = String()
        msg.data = to_json(out)
        self._pub.publish(msg)

        if int(now_t) % 10 == 0:
            self.get_logger().info(
                f"Mimicry - active:{self._mimicry_active} "
                f"sync:{self._synchrony_level:.2f} "
                f"reso:{self._resonance_intensity:.2f} "
                f"target:{self._target_agent}"
            )


def main(args=None):
    rclpy.init(args=args)
    node = AutomaticMimicryNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
