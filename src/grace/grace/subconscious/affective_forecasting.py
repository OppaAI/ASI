"""
grace_agi/subconscious/affective_forecasting.py
Subconscious Layer — Affective Forecasting
Forecasts future emotional states from planned actions and current affect.
Models impact bias (overestimation of future emotion intensity/duration).
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.utils.schemas import AffectiveForecastState, to_json


class AffectiveForecastingNode(Node):
    def __init__(self):
        super().__init__("grace_affective_forecasting")

        self.declare_parameter("update_hz", 2.0)
        self.update_hz = self.get_parameter("update_hz").value

        self._current_valence = 0.5
        self._current_arousal = 0.3
        self._optimism_bias = 0.6
        self._pessimism_bias = 0.3
        self._forecasting_horizon = 3600.0
        self._impact_bias = 0.3
        self._last_update = time.time()
        self._forecast_active = False
        self._target_event = ""

        self._horizon_decay_rate = 0.05
        self._bias_reversion_rate = 0.01

        self.create_subscription(String, "/grace/subconscious/future_self_state",
                                 self._on_future_self, 10)
        self.create_subscription(String, "/grace/unconscious/affective_state",
                                 self._on_affective_state, 10)
        self.create_subscription(String, "/grace/conscious/executive_plan",
                                 self._on_executive_plan, 10)

        self._pub = self.create_publisher(String, "/grace/subconscious/affective_forecast", 10)
        self.create_timer(1.0 / self.update_hz, self._update_forecast)
        self.get_logger().info("Affective Forecasting ready.")

    def _on_future_self(self, msg: String):
        try:
            data = json.loads(msg.data)
            self._optimism_bias = data.get("optimism_bias", self._optimism_bias)
            self._pessimism_bias = data.get("pessimism_bias", self._pessimism_bias)
            events = data.get("upcoming_events", [])
            if events:
                self._forecast_active = True
                self._target_event = events[0].get("goal", "upcoming event")
                self._forecasting_horizon = events[0].get("time_until_seconds", self._forecasting_horizon)
        except Exception as e:
            self.get_logger().warn(f"Failed to process future self: {e}")

    def _on_affective_state(self, msg: String):
        try:
            data = json.loads(msg.data)
            self._current_valence = data.get("valence", 0.5)
            self._current_arousal = data.get("arousal", 0.3)
        except Exception as e:
            self.get_logger().warn(f"Failed to process affective state: {e}")

    def _on_executive_plan(self, msg: String):
        try:
            data = json.loads(msg.data)
            goal = data.get("goal", "")
            steps = data.get("steps", [])
            if goal:
                self._forecast_active = True
                self._target_event = goal
                duration = len(steps) * 30.0
                self._forecasting_horizon = min(86400.0, max(60.0, duration))
        except Exception as e:
            self.get_logger().warn(f"Failed to process executive plan: {e}")

    def _forecast_emotional_impact(self) -> tuple:
        if not self._forecast_active:
            return self._current_valence, self._current_arousal, 0.5

        horizon_ratio = min(1.0, self._forecasting_horizon / 86400.0)
        pred_val = self._current_valence + (0.5 - self._current_valence) * horizon_ratio * 0.3
        if pred_val > 0.5:
            pred_val = min(1.0, pred_val + self._optimism_bias * 0.2 * horizon_ratio)
        else:
            pred_val = max(0.0, pred_val - self._pessimism_bias * 0.2 * horizon_ratio)

        pred_arousal = self._current_arousal + (0.3 - self._current_arousal) * horizon_ratio * 0.4
        pred_arousal = max(0.0, min(1.0, pred_arousal))

        confidence = max(0.1, min(0.95, 1.0 - horizon_ratio * 0.4 - self._impact_bias * 0.2))
        return pred_val, pred_arousal, confidence

    def _update_forecast(self):
        now = time.time()
        dt = now - self._last_update
        self._last_update = now

        pred_v, pred_a, conf = self._forecast_emotional_impact()

        if not self._forecast_active:
            self._impact_bias = max(0.1, self._impact_bias - self._bias_reversion_rate * dt)
            self._forecasting_horizon = max(300.0, self._forecasting_horizon - 10.0 * dt)
        else:
            self._impact_bias = min(0.6, self._impact_bias + self._horizon_decay_rate * dt * 0.1)

        state = AffectiveForecastState(
            timestamp=now, forecast_active=self._forecast_active,
            target_event=self._target_event,
            predicted_valence=round(pred_v, 3), predicted_arousal=round(pred_a, 3),
            impact_bias=round(self._impact_bias, 3),
            forecasting_horizon=round(self._forecasting_horizon, 1),
            confidence=round(conf, 3),
        )
        out = String()
        out.data = to_json(state)
        self._pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = AffectiveForecastingNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
