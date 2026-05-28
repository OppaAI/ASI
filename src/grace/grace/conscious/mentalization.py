"""
grace_agi/conscious/mentalization.py
SLM node — Mentalization.
Infers the mental states of other agents (beliefs, desires, intentions) from
conscious content, sensor data, social models, and theory of mind. Models
empathic accuracy and cognitive load of perspective-taking.
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String

from grace.utils.schemas import MentalizationState, to_json
from grace.utils.ollama_client import OllamaClient

SYSTEM_PROMPT = """You are GRACE's mentalization system.
Infer the mental state of the other agent(s) from available data.
Return JSON:
{
  "target_mental_state":   str (max 40 words, inferred mind of other),
  "inference_confidence":  float 0-1,
  "perspective_taken":     str (e.g. "first_order", "second_order"),
  "empathic_accuracy":     float 0-1,
  "cognitive_load":        float 0-1
}
Reply ONLY with the JSON."""


class MentalizationNode(Node):
    def __init__(self):
        super().__init__("grace_mentalization")

        self.declare_parameter("ollama_host",  "http://localhost:11434")
        self.declare_parameter("ollama_model", "nemotron")
        self.declare_parameter("update_hz",    0.5)

        host = self.get_parameter("ollama_host").value
        model = self.get_parameter("ollama_model").value
        hz = self.get_parameter("update_hz").value

        self._llm = OllamaClient(host=host, model=model, max_tokens=150)
        self._gw = {}
        self._sensors = {}
        self._social = {}
        self._tom = {}

        self._state = MentalizationState()

        self.create_subscription(String, "/grace/conscious/global_workspace",
                                 lambda m: self._set(m, "_gw"), 10)
        self.create_subscription(String, "/grace/sensors/bundle",
                                 lambda m: self._set(m, "_sensors"), 10)
        self.create_subscription(String, "/grace/subconscious/social_model",
                                 lambda m: self._set(m, "_social"), 10)
        self.create_subscription(String, "/grace/subconscious/theory_of_mind",
                                 lambda m: self._set(m, "_tom"), 10)

        self._pub = self.create_publisher(String, "/grace/conscious/mentalization", 10)
        self.create_timer(1.0 / hz, self._update)
        self.get_logger().info("Mentalization (SLM) ready.")

    def _set(self, msg, attr):
        try:
            setattr(self, attr, json.loads(msg.data))
        except Exception:
            pass

    def _update(self):
        broadcast = self._gw.get("broadcast", "")
        social_cues = self._sensors.get("social_cues", "")
        agents = self._social.get("agents_detected", [])
        empathy = self._social.get("empathy_level", 0.5)
        tom_level = self._tom.get("tom_level", 0)
        tom_acc = self._tom.get("tom_accuracy", 0.5)

        if not broadcast and not social_cues:
            return

        prompt = (
            f"Conscious broadcast: {broadcast}\n"
            f"Social cues: {social_cues}\n"
            f"Agents detected: {json.dumps(agents)}\n"
            f"Empathy: {empathy:.2f}, ToM level: {tom_level}, ToM accuracy: {tom_acc:.2f}"
        )
        raw = self._llm.chat(prompt, system=SYSTEM_PROMPT)

        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = {
                "target_mental_state": "", "inference_confidence": 0.5,
                "perspective_taken": "", "empathic_accuracy": 0.5,
                "cognitive_load": 0.3,
            }

        self._state.target_mental_state = parsed.get("target_mental_state", "")
        self._state.inference_confidence = max(0.0, min(1.0, parsed.get("inference_confidence", 0.5)))
        self._state.perspective_taken = parsed.get("perspective_taken", "")
        self._state.empathic_accuracy = max(0.0, min(1.0, parsed.get("empathic_accuracy", 0.5)))
        self._state.cognitive_load = max(0.0, min(1.0, parsed.get("cognitive_load", 0.3)))

        out = String()
        out.data = to_json(self._state)
        self._pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = MentalizationNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
