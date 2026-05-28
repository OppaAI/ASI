"""
grace_agi/hidden_workspace/error_monitoring.py
Hidden Workspace — Error Monitoring System
Rule-based detection of errors, conflicts, and correction signals.
"""
import json
import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.utils.schemas import ErrorMonitoringState, to_json
from math import exp


class ErrorMonitoringNode(Node):
    def __init__(self):
        super().__init__("grace_error_monitoring")

        self.declare_parameter("update_hz", 1.0)
        self.update_hz = self.get_parameter("update_hz").value

        self._error_severity = 0.0
        self._error_type = ""
        self._error_sources = []
        self._conflict_severity = 0.0
        self._correction_signal = 0.0
        self._prediction_error = 0.0
        self._self_mismatch = 0.0
        self._last_update = time.time()

        self.create_subscription(String, "/grace/action/log",
                                 self._on_action_log, 10)
        self.create_subscription(String, "/grace/conscious/global_workspace",
                                 self._on_workspace, 10)
        self.create_subscription(String, "/grace/unconscious/prediction_error",
                                 self._on_prediction_error, 10)
        self.create_subscription(String, "/grace/hidden/predictive_self",
                                 self._on_predictive_self, 10)

        self._pub = self.create_publisher(String, "/grace/hidden/error_monitoring", 10)
        self.create_timer(1.0 / self.update_hz, self._tick)
        self.get_logger().info("Error Monitoring ready.")

    def _on_action_log(self, msg: String):
        try:
            d = json.loads(msg.data)
            status = d.get("status", "success")
            if status in ("failure", "error", "blocked"):
                severity = d.get("severity", 0.5)
                self._error_severity = max(self._error_severity, severity)
                self._error_type = f"action_{status}"
                self._error_sources.append(f"action:{d.get('action','unknown')}")
        except Exception:
            pass

    def _on_workspace(self, msg: String):
        try:
            d = json.loads(msg.data)
            sources = d.get("sources", [])
            if "conflict" in str(sources).lower() or "contradiction" in str(sources).lower():
                self._conflict_severity = min(1.0, self._conflict_severity + 0.2)
                self._error_type = "cognitive_conflict"
        except Exception:
            pass

    def _on_prediction_error(self, msg: String):
        try:
            d = json.loads(msg.data)
            self._prediction_error = d.get("error_magnitude", 0.0)
            if self._prediction_error > 0.4:
                self._error_severity = max(self._error_severity, self._prediction_error * 0.6)
                self._error_type = d.get("source", "prediction")
                self._error_sources.append(f"prediction:{d.get('source','unknown')}")
        except Exception:
            pass

    def _on_predictive_self(self, msg: String):
        try:
            d = json.loads(msg.data)
            self._self_mismatch = d.get("self_prediction_error", 0.0)
            if self._self_mismatch > 0.5:
                self._conflict_severity = max(self._conflict_severity, self._self_mismatch * 0.5)
                self._error_sources.append("self_prediction_mismatch")
        except Exception:
            pass

    def _tick(self):
        now = time.time()
        dt = now - self._last_update
        self._last_update = now

        err_detected = self._error_severity > 0.1
        conf_detected = self._conflict_severity > 0.1

        self._correction_signal = max(
            self._error_severity * 0.7,
            self._conflict_severity * 0.5,
        )

        decay = exp(-0.1 * dt)
        self._error_severity = max(0.0, self._error_severity * decay)
        self._conflict_severity = max(0.0, self._conflict_severity * decay)
        self._correction_signal = max(0.0, self._correction_signal * decay)

        if len(self._error_sources) > 20:
            self._error_sources = self._error_sources[-20:]

        state = ErrorMonitoringState(
            timestamp=now,
            error_detected=err_detected,
            error_severity=round(self._error_severity, 3),
            error_type=self._error_type if err_detected else "",
            conflict_detected=conf_detected,
            conflict_severity=round(self._conflict_severity, 3),
            correction_signal=round(self._correction_signal, 3),
            error_sources=list(set(self._error_sources[-10:])),
        )
        out = String()
        out.data = to_json(state)
        self._pub.publish(out)

        if err_detected and int(now) % 4 == 0:
            self.get_logger().info(
                f"Error: sev={self._error_severity:.2f} "
                f"type={self._error_type} "
                f"corr={self._correction_signal:.2f}"
            )


def main(args=None):
    rclpy.init(args=args)
    node = ErrorMonitoringNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
