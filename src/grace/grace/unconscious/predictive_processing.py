"""
grace_agi/unconscious/predictive_processing.py
ROS2 node — builds a 3-tier Bayesian prediction of the current environment
from the SensorBundle and publishes raw prediction errors.
"""
import json
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from grace.grace.utils.schemas import SensorBundle, PredictionError, to_json
from grace.grace.utils.ollama_client import OllamaClient


SYSTEM_PROMPT = """You are GRACE's predictive processing hierarchy.
Given a sensor bundle JSON, produce a JSON object with:
  "low_level_error": float 0-1  (raw sensory mismatch),
  "mid_level_error": float 0-1  (associative/contextual mismatch),
  "high_level_error": float 0-1 (abstract/conceptual mismatch),
  "source": string              (which modality drove highest error),
  "precision_weight": float 0-1 (how reliable is this signal)
Reply ONLY with the JSON object."""


class PredictiveProcessingNode(Node):
    def __init__(self):
        super().__init__("grace_predictive_processing")

        self.declare_parameter("unconscious_hz", 10.0)
        self.declare_parameter("ollama_host",    "http://localhost:11434")
        self.declare_parameter("ollama_model",   "nemotron")

        hz    = self.get_parameter("unconscious_hz").value
        host  = self.get_parameter("ollama_host").value
        model = self.get_parameter("ollama_model").value

        self._llm = OllamaClient(host=host, model=model, max_tokens=128)
        self._last_bundle: dict = {}

        # Prior predictions — updated each cycle
        self._priors = {"low": 0.0, "mid": 0.0, "high": 0.0}

        self.create_subscription(String, "/grace/sensors/bundle",
                                 self._on_bundle, 10)
        self._pub = self.create_publisher(String, "/grace/unconscious/prediction_errors", 10)
        self.create_timer(1.0 / hz, self._process)

        self.get_logger().info("PredictiveProcessing ready.")

    def _on_bundle(self, msg: String):
        try:
            self._last_bundle = json.loads(msg.data)
        except Exception:
            pass

    def _process(self):
        if not self._last_bundle:
            return

        # Ask LLM to compute prediction errors
        prompt = f"Sensor bundle: {json.dumps(self._last_bundle)}"
        raw = self._llm.chat(prompt, system=SYSTEM_PROMPT)

        try:
            parsed = json.loads(raw)
        except Exception:
            # Fallback: derive errors heuristically
            bundle = self._last_bundle
            lidar = bundle.get("lidar_nearest_m", 99.0)
            parsed = {
                "low_level_error":  max(0.0, 1.0 - lidar / 5.0),
                "mid_level_error":  0.1 if bundle.get("audio_text") else 0.0,
                "high_level_error": 0.1 if bundle.get("social_cues") else 0.0,
                "source":           "lidar" if lidar < 2.0 else "ambient",
                "precision_weight": 0.9,
            }

        # Compute combined error (precision-weighted mean)
        combined = (
            parsed["low_level_error"] * 0.5 +
            parsed["mid_level_error"] * 0.3 +
            parsed["high_level_error"] * 0.2
        )

        err = PredictionError(
            error_magnitude=round(combined, 3),
            precision_weight=parsed.get("precision_weight", 0.9),
            source=parsed.get("source", "unknown"),
            raw_signal=json.dumps(parsed),
        )

        out = String()
        out.data = to_json(err)
        self._pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = PredictiveProcessingNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
