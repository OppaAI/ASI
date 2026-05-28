"""
grace_agi/hidden_workspace/narrative_coherence.py
Hidden Workspace — Narrative Coherence Monitor (SLM node)
Assesses self-narrative coherence and detects gaps via LLM.
"""
import json
import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from grace.utils.schemas import NarrativeCoherenceState, to_json
from grace.utils.ollama_client import OllamaClient


SYSTEM_PROMPT = """You are GRACE's narrative coherence monitor.
Given the current narrative self, private reflection, and episodic memory,
assess coherence of the self-narrative. Return JSON:
  "coherence_score": float 0-1,
  "narrative_consistency": float 0-1,
  "gaps_detected": int,
  "reconciliation_strategy": string,
  "self_continuity": float 0-1
Reply ONLY with the JSON object."""


class NarrativeCoherenceNode(Node):
    def __init__(self):
        super().__init__("grace_narrative_coherence")

        self.declare_parameter("ollama_host",  "http://localhost:11434")
        self.declare_parameter("ollama_model", "nemotron")
        self.declare_parameter("update_hz", 0.33)

        host  = self.get_parameter("ollama_host").value
        model = self.get_parameter("ollama_model").value
        hz    = self.get_parameter("update_hz").value

        self._llm = OllamaClient(host=host, model=model, max_tokens=256)
        self._narrative_self = ""
        self._private_reflection = ""
        self._episodic = ""

        self.create_subscription(String, "/grace/conscious/narrative_self",
                                 self._on_narrative, 10)
        self.create_subscription(String, "/grace/hidden/private_reflection",
                                 self._on_reflection, 10)
        self.create_subscription(String, "/grace/subconscious/episodic",
                                 self._on_episodic, 10)

        self._pub = self.create_publisher(String, "/grace/hidden/narrative_coherence", 10)
        self.create_timer(1.0 / hz if hz > 0 else 3.0, self._tick)
        self.get_logger().info("Narrative Coherence (SLM) ready.")

    def _on_narrative(self, msg: String):
        try:
            self._narrative_self = json.loads(msg.data).get("inner_monologue", "")
        except Exception:
            pass

    def _on_reflection(self, msg: String):
        try:
            d = json.loads(msg.data)
            self._private_reflection = d.get("reflection_text", "")[:200]
        except Exception:
            pass

    def _on_episodic(self, msg: String):
        try:
            self._episodic = json.loads(msg.data).get("content", "")[:200]
        except Exception:
            pass

    def _tick(self):
        if not self._narrative_self:
            return

        prompt = (f"Narrative self: {self._narrative_self[:200]}\n"
                  f"Private reflection: {self._private_reflection}\n"
                  f"Episodic memory: {self._episodic}")
        raw = self._llm.chat(prompt, system=SYSTEM_PROMPT)
        try:
            parsed = json.loads(raw)
            state = NarrativeCoherenceState(
                timestamp=time.time(),
                coherence_score=round(float(parsed.get("coherence_score", 0.7)), 3),
                narrative_consistency=round(float(parsed.get("narrative_consistency", 0.6)), 3),
                gaps_detected=int(parsed.get("gaps_detected", 0)),
                reconciliation_strategy=parsed.get("reconciliation_strategy", ""),
                self_continuity=round(float(parsed.get("self_continuity", 0.7)), 3),
            )
        except Exception:
            state = NarrativeCoherenceState(
                timestamp=time.time(),
                coherence_score=0.5, narrative_consistency=0.5,
                gaps_detected=0, reconciliation_strategy="defer",
                self_continuity=0.5,
            )

        out = String()
        out.data = to_json(state)
        self._pub.publish(out)

        if state.gaps_detected > 2:
            self.get_logger().warn(
                f"Narrative gaps: {state.gaps_detected} "
                f"coherence={state.coherence_score:.2f}"
            )


def main(args=None):
    rclpy.init(args=args)
    node = NarrativeCoherenceNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
