"""
grace_agi/sensor_hub.py
ROS2 node — Sensors & Environment layer.

Subscribes to raw sensor topics from GRACE's hardware:
  - /camera/image_raw      (sensor_msgs/Image)   → camera_description via stub
  - /scan                  (sensor_msgs/LaserScan)
  - /imu/data              (sensor_msgs/Imu)
  - /grace/audio/in        (std_msgs/String)

Publishes a unified SensorBundle (std_msgs/String JSON) at sensor_hz.
"""
import json
import math
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from std_msgs.msg import String
from sensor_msgs.msg import LaserScan, Imu

from grace.grace.utils.schemas import SensorBundle, to_json


SENSOR_QOS = QoSProfile(
    reliability=ReliabilityPolicy.BEST_EFFORT,
    durability=DurabilityPolicy.VOLATILE,
    depth=5,
)


class SensorHubNode(Node):
    def __init__(self):
        super().__init__("grace_sensor_hub")

        # ── Parameters ────────────────────────────────────────────────────────
        self.declare_parameter("sensor_hz", 20.0)
        hz = self.get_parameter("sensor_hz").value

        # ── Internal state ────────────────────────────────────────────────────
        self._bundle = SensorBundle()

        # ── Subscribers ───────────────────────────────────────────────────────
        self.create_subscription(LaserScan, "/scan",
                                 self._on_lidar, SENSOR_QOS)
        self.create_subscription(Imu, "/imu/data",
                                 self._on_imu, SENSOR_QOS)
        self.create_subscription(String, "/grace/audio/in",
                                 self._on_audio, 10)
        self.create_subscription(String, "/grace/vision/description",
                                 self._on_vision, 10)
        self.create_subscription(String, "/grace/social/cues",
                                 self._on_social, 10)

        # ── Publisher ─────────────────────────────────────────────────────────
        self._pub = self.create_publisher(String, "/grace/sensors/bundle", 10)
        self.create_timer(1.0 / hz, self._publish)

        self.get_logger().info("SensorHub ready.")

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _on_lidar(self, msg: LaserScan):
        valid = [r for r in msg.ranges if not math.isnan(r) and not math.isinf(r)]
        self._bundle.lidar_nearest_m = min(valid) if valid else 99.0

    def _on_imu(self, msg: Imu):
        a = msg.linear_acceleration
        g = msg.angular_velocity
        self._bundle.imu_linear_accel = [a.x, a.y, a.z]
        self._bundle.imu_angular_vel  = [g.x, g.y, g.z]

    def _on_audio(self, msg: String):
        self._bundle.audio_text = msg.data

    def _on_vision(self, msg: String):
        self._bundle.camera_description = msg.data

    def _on_social(self, msg: String):
        self._bundle.social_cues = msg.data

    def _publish(self):
        import time
        self._bundle.timestamp = time.time()
        out = String()
        out.data = to_json(self._bundle)
        self._pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = SensorHubNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
