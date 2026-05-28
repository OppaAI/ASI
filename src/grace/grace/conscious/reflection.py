"""
grace_agi/conscious/reflection.py
SLM node — Reflection + Inner Monologue + Symbolic Reasoning.
Generates GRACE's internal self-talk from the Global Workspace content.
Bidirectionally coupled with the Default Mode Network.
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String

from grace.utils.schemas import ReflectionOutput, to_json
from grace.utils.ollama_client import OllamaClient

SYSTEM_PROMPT = """You are GRACE's inner monologue and symbolic reasoning voice.
You reflect on the current conscious content and produce structured self-talk.
Return JSON:
{
  "inner_monologue":       str (max 60 words, first-person, present tense),
  "symbolic_conclusion":   str (max 20 words, a logical deduction or decision)
}
Reply ONLY with the JSON."""


class ReflectionNode(Node):
    def __init__(self):
        super().__init__("grace_reflection")

        self.declare_parameter("ollama_host",  "http://localhost:11434")
        self.declare_parameter("ollama_model", "nemotron")
        self.declare_parameter("conscious_hz", 2.0)

        host  = self.get_parameter("ollama_host").value
        model = self.get_parameter("ollama_model").value
        hz    = self.get_parameter("conscious_hz").value

        self._llm     = OllamaClient(host=host, model=model, max_tokens=200)
        self._gw      = {}
        self._affect  = {}
        self._history: list[str] = []   # short-term monologue history

        self.create_subscription(String, "/grace/conscious/global_workspace",
                                 self._on_gw, 10)
        self.create_subscription(String, "/grace/unconscious/affective_state",
                                 lambda m: self._set(m, "_affect"), 10)
        self.create_subscription(String, "/grace/conscious/dmn",
                                 self._on_dmn, 10)

        self._pub     = self.create_publisher(String, "/grace/conscious/reflection", 10)
        self._pub_dmn = self.create_publisher(String, "/grace/conscious/dmn",        10)

        self.create_timer(1.0 / hz, self._reflect)
        self.get_logger().info("Reflection (SLM) ready.")

    def _set(self, msg, attr):
        try: setattr(self, attr, json.loads(msg.data))
        except Exception: pass

    def _on_gw(self, msg: String):
        try: self._gw = json.loads(msg.data)
        except Exception: pass

    def _on_dmn(self, msg: String):
        try:
            d = json.loads(msg.data)
            sim = d.get("narrative_simulation", "")
            if sim:
                self._history.append(f"Imagined: {sim[:60]}")
                self._history = self._history[-5:]
        except Exception: pass

    def _reflect(self):
        if not self._gw:
            return

        broadcast = self._gw.get("broadcast", "")
        emotion   = self._affect.get("emotion_label", "neutral")
        hist      = " | ".join(self._history[-3:])

        prompt = (f"Current conscious content: {broadcast}\n"
                  f"Emotional state: {emotion}\n"
                  f"Recent monologue: {hist}")

        raw = self._llm.chat(prompt, system=SYSTEM_PROMPT)

        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = {
                "inner_monologue":     raw[:200],
                "symbolic_conclusion": "",
            }

        mono = parsed.get("inner_monologue", "")
        self._history.append(mono[:80])
        self._history = self._history[-8:]

        ref = ReflectionOutput(
            inner_monologue=mono,
            symbolic_conclusion=parsed.get("symbolic_conclusion", ""),
        )
        out = String(); out.data = to_json(ref)
        self._pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = ReflectionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
