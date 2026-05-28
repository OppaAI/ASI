"""
grace_agi/sensors/proprioceptive.py
Sensors Layer — Proprioceptive Node
Position · Orientation · Velocity · Embodied Orientation
Rule-based integration from IMU data and velocity commands.
"""
import json, math, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.utils.schemas import ProprioceptiveState, to_json


class ProprioceptiveNode(Node):
    def __init__(self):
        super().__init__("grace_proprioceptive")

        # ── Parameters ────────────────────────────────────────────────────────
        self.declare_parameter("update_hz", 5.0)
        self.update_hz = self.get_parameter("update_hz").value

        # ── Internal State ───────────────────────────────────────────────────
        self._position_x = 0.0
        self._position_y = 0.0
        self._orientation = 0.0
        self._velocity_linear = 0.0
        self._velocity_angular = 0.0
        self._last_update = time.time()

        # ── Subscribers ──────────────────────────────────────────────────────
        self.create_subscription(String, "/grace/sensors/bundle",
                                 self._on_bundle, 10)
        self.create_subscription(String, "/cmd_vel",
                                 self._on_cmd_vel, 10)

        # ── Publisher ─────────────────────────────────────────────────────────
        self._pub = self.create_publisher(String, "/grace/sensors/proprioceptive", 10)
        self.create_timer(1.0 / self.update_hz, self._update_proprioceptive)
        self.get_logger().info("Proprioceptive Node ready.")

    def _on_bundle(self, msg: String):
        try:
            data = json.loads(msg.data)
            accel = data.get("imu_linear_accel", [0.0, 0.0, 0.0])
            gyro = data.get("imu_angular_vel", [0.0, 0.0, 0.0])
            self._velocity_linear = math.sqrt(accel[0]**2 + accel[1]**2 + accel[2]**2)
            self._velocity_angular = abs(gyro[2])
            camera_desc = data.get("camera_description", "")
            if camera_desc:
                desc_lower = camera_desc.lower()
                if "flower" in desc_lower or "garden" in desc_lower:
                    self._embodied_location_cached = "in a garden"
                elif "trail" in desc_lower or "path" in desc_lower:
                    self._embodied_location_cached = "on a trail"
                elif "indoor" in desc_lower or "room" in desc_lower:
                    self._embodied_location_cached = "indoors"
                else:
                    self._embodied_location_cached = "outdoors"
        except Exception as e:
            self.get_logger().warn(f"Failed to process bundle: {e}")

    def _on_cmd_vel(self, msg: String):
        try:
            data = json.loads(msg.data)
            self._velocity_linear = abs(data.get("linear", {}).get("x", self._velocity_linear))
            self._velocity_angular = abs(data.get("angular", {}).get("z", self._velocity_angular))
            self._orientation += data.get("angular", {}).get("z", 0.0) * 0.1
            self._orientation = self._orientation % (2.0 * math.pi)
            linear = data.get("linear", {}).get("x", 0.0)
            self._position_x += linear * math.cos(self._orientation) * 0.05
            self._position_y += linear * math.sin(self._orientation) * 0.05
        except Exception as e:
            self.get_logger().warn(f"Failed to process cmd_vel: {e}")

    def _orientation_to_heading(self) -> str:
        angle = self._orientation % (2.0 * math.pi)
        if angle < 0.35 or angle > 5.93:
            return "facing_north"
        elif angle < 1.05:
            return "facing_northeast"
        elif angle < 1.75:
            return "facing_east"
        elif angle < 2.45:
            return "facing_southeast"
        elif angle < 3.15:
            return "facing_south"
        elif angle < 3.85:
            return "facing_southwest"
        elif angle < 4.55:
            return "facing_west"
        else:
            return "facing_northwest"

    def _update_proprioceptive(self):
        now = time.time()
        dt = now - self._last_update
        self._last_update = now

        # Decay velocity when no commands received
        self._velocity_linear = max(0.0, self._velocity_linear - 0.5 * dt)
        self._velocity_angular = max(0.0, self._velocity_angular - 1.0 * dt)

        loc = getattr(self, "_embodied_location_cached", "unknown")

        state = ProprioceptiveState(
            timestamp=now,
            position_x=round(self._position_x, 2),
            position_y=round(self._position_y, 2),
            orientation=round(self._orientation, 3),
            velocity_linear=round(self._velocity_linear, 3),
            velocity_angular=round(self._velocity_angular, 3),
            embodied_orientation=self._orientation_to_heading(),
            location_description=loc,
        )
        out = String()
        out.data = to_json(state)
        self._pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = ProprioceptiveNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
