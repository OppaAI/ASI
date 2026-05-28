"""
grace_agi/hidden_workspace/predictive_self_model.py
Hidden Workspace — Predictive Self-Model (SLM node)
Detects self-prediction errors and monitors self-model coherence via LLM.
"""
import json
import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from grace.utils.schemas import PredictiveSelfModelState, to_json
from grace.utils.ollama_client import OllamaClient


SYSTEM_PROMPT = """You are GRACE's predictive self-model monitor.
Given the current conscious content, affective state, and episodic memory,
detect self-prediction errors and assess self-model coherence.
Return JSON:
  "self_prediction_error": float 0-1,
  "self_model_coherence": float 0-1,
  "agency_signal": float 0-1,
  "ownership_signal": float 0-1
Reply ONLY with the JSON object."""


class PredictiveSelfModelNode(Node):
    def __init__(self):
        super().__init__("grace_predictive_self_model")

        self.declare_parameter("ollama_host",  "http://localhost:11434")
        self.declare_parameter("ollama_model", "nemotron")
        self.declare_parameter("update_hz", 0.5)

        host  = self.get_parameter("ollama_host").value
        model = self.get_parameter("ollama_model").value
        hz    = self.get_parameter("update_hz").value

        self._llm = OllamaClient(host=host, model=model, max_tokens=192)
        self._workspace = ""
        self._affect = ""
        self._episodic = ""
        self._last_state = PredictiveSelfModelState(
            self_prediction_error=0.0,
            self_model_coherence=0.7,
            agency_signal=0.8,
            ownership_signal=0.7,
        )

        self.create_subscription(String, "/grace/conscious/global_workspace",
                                 self._on_workspace, 10)
        self.create_subscription(String, "/grace/unconscious/affective_state",
                                 self._on_affect, 10)
        self.create_subscription(String, "/grace/subconscious/episodic",
                                 self._on_episodic, 10)

        self._pub = self.create_publisher(String, "/grace/hidden/predictive_self", 10)
        self.create_timer(1.0 / hz if hz > 0 else 2.0, self._tick)
        self.get_logger().info("Predictive Self-Model (SLM) ready.")

    def _on_workspace(self, msg: String):
        try:
            self._workspace = json.loads(msg.data).get("broadcast", "")
        except Exception:
            pass

    def _on_affect(self, msg: String):
        try:
            d = json.loads(msg.data)
            self._affect = (f"V={d.get('valence',0.5):.2f} "
                            f"A={d.get('arousal',0.3):.2f} "
                            f"E={d.get('emotion_label','neutral')}")
        except Exception:
            pass

    def _on_episodic(self, msg: String):
        try:
            self._episodic = json.loads(msg.data).get("content", "")[:150]
        except Exception:
            pass

    def _tick(self):
        if not self._workspace:
            return

        prompt = (f"Conscious: {self._workspace[:200]}\n"
                  f"Affect: {self._affect}\n"
                  f"Episodic: {self._episodic}")
        raw = self._llm.chat(prompt, system=SYSTEM_PROMPT)
        try:
            parsed = json.loads(raw)
            state = PredictiveSelfModelState(
                timestamp=time.time(),
                self_prediction_error=round(float(parsed.get("self_prediction_error", 0.0)), 3),
                self_model_coherence=round(float(parsed.get("self_model_coherence", 0.7)), 3),
                agency_signal=round(float(parsed.get("agency_signal", 0.8)), 3),
                ownership_signal=round(float(parsed.get("ownership_signal", 0.7)), 3),
            )
            self._last_state = state
        except Exception:
            self._last_state.timestamp = time.time()
            # Gradual decay toward baseline coherence
            self._last_state.self_model_coherence = round(
                min(0.8, self._last_state.self_model_coherence + 0.01), 3
            )
            state = self._last_state

        out = String()
        out.data = to_json(state)
        self._pub.publish(out)

        if state.self_prediction_error > 0.6:
            self.get_logger().warn(
                f"High self-prediction error: {state.self_prediction_error:.2f}"
            )


def main(args=None):
    rclpy.init(args=args)
    node = PredictiveSelfModelNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
