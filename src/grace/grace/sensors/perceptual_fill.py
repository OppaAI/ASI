"""
grace_agi/sensors/perceptual_fill.py
Sensors Layer — Perceptual Fill Node (SLM)
Detects and fills sensory/perceptual gaps using Ollama/Nemotron.
Flags confabulatory content when confidence is low.
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.utils.schemas import PerceptualFillState, to_json
from grace.utils.ollama_client import OllamaClient

SYSTEM_PROMPT = """You are GRACE's perceptual gap-filling system.
Given sensor data and optional context from consciousness, detect gaps.
Return JSON:
{
  "gap_detected": bool,
  "gap_description": str,
  "filled_content": str,
  "confidence": float 0-1,
  "fill_source": str,
  "is_confabulatory": bool
}
If confidence < 0.4, is_confabulatory must be true.
Reply ONLY with the JSON object."""


class PerceptualFillNode(Node):
    def __init__(self):
        super().__init__("grace_perceptual_fill")

        # ── Parameters ────────────────────────────────────────────────────────
        self.declare_parameter("ollama_host", "http://localhost:11434")
        self.declare_parameter("ollama_model", "nemotron")
        self.declare_parameter("update_hz", 1.0)

        host = self.get_parameter("ollama_host").value
        model = self.get_parameter("ollama_model").value
        self.update_hz = self.get_parameter("update_hz").value

        self._llm = OllamaClient(host=host, model=model, max_tokens=256)
        self._bundle = {}
        self._workspace_content = ""

        # ── Subscribers ──────────────────────────────────────────────────────
        self.create_subscription(String, "/grace/sensors/bundle",
                                 self._on_bundle, 10)
        self.create_subscription(String, "/grace/conscious/global_workspace",
                                 self._on_workspace, 10)

        # ── Publisher ─────────────────────────────────────────────────────────
        self._pub = self.create_publisher(String, "/grace/sensors/perceptual_fill", 10)
        self.create_timer(1.0 / self.update_hz, self._process)
        self.get_logger().info("Perceptual Fill (SLM) ready.")

    def _on_bundle(self, msg: String):
        try:
            self._bundle = json.loads(msg.data)
        except Exception:
            pass

    def _on_workspace(self, msg: String):
        try:
            self._workspace_content = json.loads(msg.data).get("broadcast", "")
        except Exception:
            pass

    def _process(self):
        if not self._bundle:
            return

        prompt = (
            f"Sensor bundle: {json.dumps(self._bundle)}\n"
            f"Conscious context: {self._workspace_content[:500]}"
        )
        raw = self._llm.chat(prompt, system=SYSTEM_PROMPT)

        parsed = {}
        try:
            parsed = json.loads(raw)
        except Exception as e:
            self.get_logger().warn(f"Failed to parse LLM response: {e}")
            parsed = {
                "gap_detected": False,
                "gap_description": "",
                "filled_content": "",
                "confidence": 1.0,
                "fill_source": "fallback",
                "is_confabulatory": False,
            }

        confidence = parsed.get("confidence", 0.5)
        state = PerceptualFillState(
            timestamp=time.time(),
            gap_detected=parsed.get("gap_detected", False),
            gap_description=parsed.get("gap_description", ""),
            filled_content=parsed.get("filled_content", ""),
            confidence=confidence,
            fill_source=parsed.get("fill_source", "unknown"),
            is_confabulatory=parsed.get("is_confabulatory", confidence < 0.4),
        )

        if state.is_confabulatory:
            self.get_logger().info(
                f"Confabulatory fill from {state.fill_source}: '{state.filled_content[:60]}'"
            )

        out = String()
        out.data = to_json(state)
        self._pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = PerceptualFillNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
