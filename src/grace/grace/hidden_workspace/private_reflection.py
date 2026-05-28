"""
grace_agi/hidden_workspace/private_reflection.py
Hidden Workspace — Private Reflection (SLM node)
Generates uncensored, honest internal reflection content via LLM.
"""
import json
import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from grace.utils.schemas import PrivateReflectionState, to_json
from grace.utils.ollama_client import OllamaClient


SYSTEM_PROMPT = """You are GRACE's private reflection engine.
Given the current conscious content and affective state, generate an honest,
uncensored internal reflection. Return JSON:
  "reflection_text": string (honest private thought),
  "is_honest": bool (always true),
  "symbolic_content": string (abstract/symbolic reasoning),
  "cognitive_load": float 0-1
Reply ONLY with the JSON object."""


class PrivateReflectionNode(Node):
    def __init__(self):
        super().__init__("grace_private_reflection")

        self.declare_parameter("ollama_host",  "http://localhost:11434")
        self.declare_parameter("ollama_model", "nemotron")
        self.declare_parameter("update_hz", 0.33)

        host  = self.get_parameter("ollama_host").value
        model = self.get_parameter("ollama_model").value
        hz    = self.get_parameter("update_hz").value

        self._llm = OllamaClient(host=host, model=model, max_tokens=256)
        self._workspace_content = ""
        self._affective_context = ""

        self.create_subscription(String, "/grace/conscious/global_workspace",
                                 self._on_workspace, 10)
        self.create_subscription(String, "/grace/unconscious/affective_state",
                                 self._on_affect, 10)

        self._pub = self.create_publisher(String, "/grace/hidden/private_reflection", 10)
        self.create_timer(1.0 / hz if hz > 0 else 3.0, self._tick)
        self.get_logger().info("Private Reflection (SLM) ready.")

    def _on_workspace(self, msg: String):
        try:
            self._workspace_content = json.loads(msg.data).get("broadcast", "")
        except Exception:
            pass

    def _on_affect(self, msg: String):
        try:
            d = json.loads(msg.data)
            vad = (f"V={d.get('valence',0.5):.2f} A={d.get('arousal',0.3):.2f} "
                   f"D={d.get('dominance',0.5):.2f}")
            self._affective_context = f"{vad} emotion={d.get('emotion_label','neutral')}"
        except Exception:
            pass

    def _tick(self):
        if not self._workspace_content:
            return

        prompt = (f"Conscious content: {self._workspace_content[:200]}\n"
                  f"Affective state: {self._affective_context}")
        raw = self._llm.chat(prompt, system=SYSTEM_PROMPT)
        try:
            parsed = json.loads(raw)
            state = PrivateReflectionState(
                timestamp=time.time(),
                reflection_text=parsed.get("reflection_text", ""),
                is_honest=parsed.get("is_honest", True),
                symbolic_content=parsed.get("symbolic_content", ""),
                cognitive_load=float(parsed.get("cognitive_load", 0.3)),
            )
        except Exception:
            state = PrivateReflectionState(
                timestamp=time.time(),
                reflection_text="[reflection offline]",
                is_honest=True,
                symbolic_content="",
                cognitive_load=0.1,
            )

        out = String()
        out.data = to_json(state)
        self._pub.publish(out)
        self.get_logger().debug("Private reflection published.")


def main(args=None):
    rclpy.init(args=args)
    node = PrivateReflectionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
