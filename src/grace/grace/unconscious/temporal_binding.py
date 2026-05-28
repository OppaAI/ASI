"""
grace_agi/unconscious/temporal_binding.py
Unconscious Layer — Temporal Binding
Integrates signals within a ~500ms temporal window
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.utils.schemas import TemporalBindingState, to_json


class TemporalBindingNode(Node):
    def __init__(self):
        super().__init__("grace_temporal_binding")

        self.declare_parameter("update_hz", 2.0)
        self.update_hz = self.get_parameter("update_hz").value

        self._binding_window_ms = 500.0
        self._signals = []
        self._coherence = 0.7
        self._asynchrony_detected = False
        self._last_update = time.time()

        self.create_subscription(String, "/grace/sensors/bundle",
                                 self._on_sensor_bundle, 10)
        self.create_subscription(String, "/grace/unconscious/thalamic_broadcast",
                                 self._on_thalamic_broadcast, 10)

        self._pub = self.create_publisher(String, "/grace/unconscious/temporal_binding", 10)
        self.create_timer(1.0 / self.update_hz, self._update_binding)
        self.get_logger().info("Temporal Binding ready.")

    def _on_sensor_bundle(self, msg: String):
        try:
            data = json.loads(msg.data)
            now_t = data.get("timestamp", time.time())
            self._signals.append({
                "type": "sensor",
                "content": data.get("camera_description", ""),
                "ts": now_t,
            })
        except Exception as e:
            self.get_logger().warn(f"Failed to process sensor bundle: {e}")

    def _on_thalamic_broadcast(self, msg: String):
        try:
            data = json.loads(msg.data)
            now_t = data.get("timestamp", time.time())
            self._signals.append({
                "type": "thalamic",
                "content": data.get("content", ""),
                "ts": now_t,
            })
        except Exception as e:
            self.get_logger().warn(f"Failed to process thalamic broadcast: {e}")

    def _update_binding(self):
        now_t = time.time()
        dt = now_t - self._last_update
        self._last_update = now_t

        cutoff = now_t - self._binding_window_ms / 1000.0
        self._signals = [s for s in self._signals if s["ts"] >= cutoff]

        timestamps = [s["ts"] for s in self._signals]
        if len(timestamps) >= 2:
            spread = max(timestamps) - min(timestamps)
            self._asynchrony_detected = spread > self._binding_window_ms / 1000.0 * 0.8
            ideal_spread = self._binding_window_ms / 1000.0
            self._coherence = max(0.0, min(1.0, 1.0 - abs(spread - ideal_spread * 0.5) / ideal_spread))
        else:
            self._asynchrony_detected = False
            self._coherence = 0.7 if self._signals else 0.0

        bound = [s["content"] for s in self._signals if s["content"]]

        out = TemporalBindingState(
            timestamp=now_t,
            binding_window_ms=self._binding_window_ms,
            signals_bound=bound,
            coherence=self._coherence,
            num_signals=len(self._signals),
            asynchrony_detected=self._asynchrony_detected,
        )
        msg = String()
        msg.data = to_json(out)
        self._pub.publish(msg)

        if int(now_t) % 10 == 0:
            self.get_logger().info(
                f"Temporal Bind - sig:{len(self._signals)} "
                f"coh:{self._coherence:.2f} "
                f"async:{self._asynchrony_detected}"
            )


def main(args=None):
    rclpy.init(args=args)
    node = TemporalBindingNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
