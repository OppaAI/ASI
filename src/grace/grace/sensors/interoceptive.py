"""
grace_agi/sensors/interoceptive.py
Sensors Layer — Interoceptive Node
Fatigue · Bodily Arousal · Tension · Heartbeat · Breathing
Rule-based integration from sensor bundle and vital core data.
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.utils.schemas import InteroceptiveState, to_json


class InteroceptiveNode(Node):
    def __init__(self):
        super().__init__("grace_interoceptive")

        # ── Parameters ────────────────────────────────────────────────────────
        self.declare_parameter("update_hz", 2.0)
        self.update_hz = self.get_parameter("update_hz").value

        # ── Internal State ───────────────────────────────────────────────────
        self._fatigue = 0.0
        self._hunger = 0.0
        self._arousal = 0.3
        self._pain = 0.0
        self._temperature = 0.5
        self._tension = 0.2
        self._heartbeat_rapidity = 0.3
        self._breathing_rate = 0.3
        self._last_update = time.time()

        # ── Decay parameters ─────────────────────────────────────────────────
        self._fatigue_decay = 0.03
        self._arousal_decay = 0.04
        self._tension_decay = 0.05
        self._heartbeat_decay = 0.04
        self._breathing_decay = 0.04
        self._temperature_decay = 0.01

        # ── Subscribers ──────────────────────────────────────────────────────
        self.create_subscription(String, "/grace/sensors/bundle",
                                 self._on_bundle, 10)
        self.create_subscription(String, "/grace/vital/pain_signal",
                                 self._on_pain, 10)
        self.create_subscription(String, "/grace/vital/metabolic_resource",
                                 self._on_metabolic, 10)

        # ── Publisher ─────────────────────────────────────────────────────────
        self._pub = self.create_publisher(String, "/grace/sensors/interoceptive", 10)
        self.create_timer(1.0 / self.update_hz, self._update_interoceptive)
        self.get_logger().info("Interoceptive Node ready.")

    def _on_bundle(self, msg: String):
        try:
            data = json.loads(msg.data)
            accel = data.get("imu_linear_accel", [0.0, 0.0, 0.0])
            movement = sum(abs(v) for v in accel)
            self._arousal = min(1.0, self._arousal + movement * 0.02)
            self._heartbeat_rapidity = min(1.0, self._heartbeat_rapidity + movement * 0.015)
            self._breathing_rate = min(1.0, self._breathing_rate + movement * 0.01)
            battery = data.get("battery_pct", 100.0)
            if battery < 20.0:
                self._fatigue = min(1.0, self._fatigue + 0.05)
        except Exception as e:
            self.get_logger().warn(f"Failed to process bundle: {e}")

    def _on_pain(self, msg: String):
        try:
            data = json.loads(msg.data)
            self._pain = data.get("pain_intensity", 0.0)
            if self._pain > 0.3:
                self._tension = min(1.0, self._tension + self._pain * 0.2)
                self._heartbeat_rapidity = min(1.0, self._heartbeat_rapidity + self._pain * 0.15)
                self._breathing_rate = min(1.0, self._breathing_rate + self._pain * 0.1)
        except Exception as e:
            self.get_logger().warn(f"Failed to process pain signal: {e}")

    def _on_metabolic(self, msg: String):
        try:
            data = json.loads(msg.data)
            glucose = data.get("glucose_equivalent", 1.0)
            self._fatigue = min(1.0, self._fatigue + (1.0 - glucose) * 0.3)
            self._hunger = max(0.0, 1.0 - glucose)
        except Exception as e:
            self.get_logger().warn(f"Failed to process metabolic resource: {e}")

    def _update_interoceptive(self):
        now = time.time()
        dt = now - self._last_update
        self._last_update = now

        # Natural decay toward baseline
        self._fatigue = max(0.0, self._fatigue - self._fatigue_decay * dt)
        self._arousal = self._arousal + (0.3 - self._arousal) * self._arousal_decay * dt
        self._tension = max(0.2, self._tension - self._tension_decay * dt)
        self._heartbeat_rapidity = self._heartbeat_rapidity + (0.3 - self._heartbeat_rapidity) * self._heartbeat_decay * dt
        self._breathing_rate = self._breathing_rate + (0.3 - self._breathing_rate) * self._breathing_decay * dt
        self._temperature = self._temperature + (0.5 - self._temperature) * self._temperature_decay * dt
        self._pain = max(0.0, self._pain - 0.02 * dt)

        state = InteroceptiveState(
            timestamp=now,
            fatigue=round(self._fatigue, 3),
            hunger=round(self._hunger, 3),
            arousal=round(self._arousal, 3),
            pain=round(self._pain, 3),
            temperature=round(self._temperature, 3),
            tension=round(self._tension, 3),
            heartbeat_rapidity=round(self._heartbeat_rapidity, 3),
            breathing_rate=round(self._breathing_rate, 3),
        )
        out = String()
        out.data = to_json(state)
        self._pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = InteroceptiveNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
