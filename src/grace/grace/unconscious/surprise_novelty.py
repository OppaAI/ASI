"""
grace_agi/unconscious/surprise_novelty.py
Unconscious Layer — Surprise & Novelty Detection
Prediction error monitoring · Novelty detection · Habituation · Orienting response
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.utils.schemas import SurpriseState, to_json


class SurpriseNoveltyNode(Node):
    def __init__(self):
        super().__init__("grace_surprise_novelty")

        self.declare_parameter("update_hz", 2.0)
        self.update_hz = self.get_parameter("update_hz").value
        self.declare_parameter("surprise_threshold", 0.4)
        self._surprise_threshold = self.get_parameter("surprise_threshold").value

        self._surprise_level = 0.0
        self._novelty_level = 0.0
        self._mismatch_magnitude = 0.0
        self._orienting_response = False
        self._source_modality = ""
        self._habituation_factor = 1.0
        self._recent_inputs = []
        self._familiarity_map = {}
        self._last_update = time.time()

        self.create_subscription(String, "/grace/unconscious/prediction_error",
                                 self._on_prediction_error, 10)
        self.create_subscription(String, "/grace/sensors/bundle",
                                 self._on_sensor_bundle, 10)

        self._pub = self.create_publisher(String, "/grace/unconscious/surprise_state", 10)
        self.create_timer(1.0 / self.update_hz, self._update_surprise)
        self.get_logger().info("Surprise & Novelty ready.")

    def _on_prediction_error(self, msg: String):
        try:
            data = json.loads(msg.data)
            self._mismatch_magnitude = data.get("error_magnitude", 0.0)
            self._source_modality = data.get("source", "")
        except Exception as e:
            self.get_logger().warn(f"Failed to process prediction error: {e}")

    def _on_sensor_bundle(self, msg: String):
        try:
            data = json.loads(msg.data)
            desc = data.get("camera_description", "")
            audio = data.get("audio_text", "")
            cue = f"{desc}|{audio}"
            if cue:
                self._recent_inputs.append(cue)
                self._recent_inputs = self._recent_inputs[-20:]
                self._familiarity_map[cue] = self._familiarity_map.get(cue, 0) + 1
        except Exception as e:
            self.get_logger().warn(f"Failed to process sensor bundle: {e}")

    def _update_surprise(self):
        now_t = time.time()
        dt = now_t - self._last_update
        self._last_update = now_t

        novelty_sum = 0.0
        for cue, count in self._familiarity_map.items():
            novelty_sum += count
        avg_familiarity = novelty_sum / max(len(self._familiarity_map), 1)
        self._novelty_level = max(0.0, min(1.0, 1.0 - avg_familiarity / max(avg_familiarity, 1.0)))

        self._surprise_level = self._mismatch_magnitude * self._habituation_factor
        self._surprise_level = max(0.0, min(1.0, self._surprise_level))

        self._orienting_response = self._surprise_level > self._surprise_threshold

        self._habituation_factor = max(0.1, self._habituation_factor - 0.02 * dt)
        if self._mismatch_magnitude > 0.3:
            self._habituation_factor = min(1.0, self._habituation_factor + 0.1)

        out = SurpriseState(
            timestamp=now_t,
            surprise_level=self._surprise_level,
            novelty_level=self._novelty_level,
            mismatch_magnitude=self._mismatch_magnitude,
            orienting_response=self._orienting_response,
            source_modality=self._source_modality,
            habituation_factor=self._habituation_factor,
        )
        msg = String()
        msg.data = to_json(out)
        self._pub.publish(msg)

        if int(now_t) % 10 == 0:
            self.get_logger().info(
                f"Surprise - surp:{self._surprise_level:.2f} "
                f"novel:{self._novelty_level:.2f} "
                f"orient:{self._orienting_response} "
                f"hab:{self._habituation_factor:.2f}"
            )


def main(args=None):
    rclpy.init(args=args)
    node = SurpriseNoveltyNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
