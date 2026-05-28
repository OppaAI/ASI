"""
grace_agi/sensors/temporal_calibration.py
Sensors Layer — Temporal Calibration Node
Internal clock drift estimation and calibration accuracy.
Rule-based drift model with self-contained timing.
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.utils.schemas import TemporalCalibrationState, to_json


class TemporalCalibrationNode(Node):
    def __init__(self):
        super().__init__("grace_temporal_calibration")

        # ── Parameters ────────────────────────────────────────────────────────
        self.declare_parameter("update_hz", 1.0)
        self.update_hz = self.get_parameter("update_hz").value

        # ── Internal State ───────────────────────────────────────────────────
        self._internal_clock_ms = 0.0
        self._wall_clock_start = time.time()
        self._drift_rate = 0.002
        self._drift_jitter = 0.0005
        self._last_update = time.time()
        self._calibration_accuracy = 1.0
        self._drift_samples = [0.002]
        self._sample_count = 0

        # ── Publisher (no subscribers — self-contained) ──────────────────────
        self._pub = self.create_publisher(String, "/grace/sensors/temporal_calibration", 10)
        self.create_timer(1.0 / self.update_hz, self._update_calibration)
        self.get_logger().info("Temporal Calibration Node ready.")

    def _update_calibration(self):
        now = time.time()
        dt = now - self._last_update
        self._last_update = now

        # Advance internal clock with drift
        drift_this_cycle = self._drift_rate + self._drift_jitter * (hash(str(now)) % 100 - 50) / 50.0
        self._internal_clock_ms += dt * 1000.0 * (1.0 + drift_this_cycle)

        # Update drift rate (slowly wandering Brownian motion)
        drift_noise = (hash(str(now + 1.0)) % 200 - 100) / 100000.0
        self._drift_rate = max(-0.05, min(0.05, self._drift_rate + drift_noise * dt))

        # Wall clock elapsed
        elapsed_wall = (now - self._wall_clock_start) * 1000.0

        # Recalibrate periodically: compare internal to wall clock
        self._sample_count += 1
        if self._sample_count % 10 == 0:
            measured_drift = (self._internal_clock_ms - elapsed_wall) / elapsed_wall if elapsed_wall > 0 else 0.0
            self._drift_samples.append(measured_drift)
            if len(self._drift_samples) > 20:
                self._drift_samples.pop(0)

            # Accuracy is 1.0 minus absolute drift relative to wall clock
            drift_error = abs(self._internal_clock_ms - elapsed_wall) / max(elapsed_wall, 1.0)
            self._calibration_accuracy = max(0.0, min(1.0, 1.0 - drift_error))

            # Correct internal clock toward wall clock to prevent unbounded drift
            correction = (elapsed_wall - self._internal_clock_ms) * 0.1
            self._internal_clock_ms += correction

        # Duration estimate based on internal clock since last tick
        duration_estimate_ms = dt * 1000.0 * (1.0 + self._drift_rate)

        state = TemporalCalibrationState(
            timestamp=now,
            internal_clock_ms=round(self._internal_clock_ms, 2),
            drift_rate=round(self._drift_rate, 6),
            duration_estimate_ms=round(duration_estimate_ms, 2),
            actual_duration_ms=round(dt * 1000.0, 2),
            calibration_accuracy=round(self._calibration_accuracy, 4),
        )

        out = String()
        out.data = to_json(state)
        self._pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = TemporalCalibrationNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
