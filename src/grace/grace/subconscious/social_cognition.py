"""
grace_agi/subconscious/social_cognition.py
SLM node — Social Cognition Network.
Theory of Mind, empathy, joint attention, norm compliance,
group dynamics, and social prediction errors — powered by Nemotron.
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String

from grace.grace.utils.schemas import SocialModel, to_json
from grace.grace.utils.memory_store import MemoryStore
from grace.grace.utils.ollama_client import OllamaClient

SYSTEM_PROMPT = """You are GRACE's social cognition system.
Given a sensor bundle and social cues, return JSON:
{
  "agents_detected":  [{"id": str, "estimated_intent": str, "emotional_state": str}],
  "group_dynamic":    str,
  "empathy_level":    float 0-1,
  "norm_compliance":  float 0-1,
  "social_prediction_error": float 0-1,
  "recommended_behavior": str
}
Reply ONLY with the JSON object."""


class SocialCognitionNode(Node):
    def __init__(self):
        super().__init__("grace_social_cognition")

        self.declare_parameter("social_db",    "/home/grace/memory/social.json")
        self.declare_parameter("ollama_host",  "http://localhost:11434")
        self.declare_parameter("ollama_model", "nemotron")

        db_path = self.get_parameter("social_db").value
        host    = self.get_parameter("ollama_host").value
        model   = self.get_parameter("ollama_model").value

        self._store  = MemoryStore(db_path, max_entries=200)
        self._llm    = OllamaClient(host=host, model=model, max_tokens=256)
        self._bundle = {}
        self._state  = SocialModel()

        self.create_subscription(String, "/grace/sensors/bundle",
                                 self._on_bundle, 10)
        self.create_subscription(String, "/grace/subconscious/social",
                                 self._on_write, 10)
        self.create_subscription(String, "/grace/dreaming/consolidation",
                                 self._on_consolidation, 10)

        self._pub = self.create_publisher(String, "/grace/subconscious/social_recall", 10)
        self.create_timer(3.0, self._process)
        self.get_logger().info("SocialCognition (SLM) ready.")

    def _on_bundle(self, msg: String):
        try: self._bundle = json.loads(msg.data)
        except Exception: pass

    def _on_write(self, msg: String):
        try:
            entry = json.loads(msg.data)
            entry["memory_type"] = "social"
            self._store.append(entry)
        except Exception: pass

    def _on_consolidation(self, msg: String):
        pass   # social learning happens via store writes

    def _process(self):
        if not self._bundle:
            return

        social_cues = self._bundle.get("social_cues", "")
        if not social_cues:
            return   # nothing social to process

        history = self._store.tail(5)
        prompt  = (f"Sensor bundle: {json.dumps(self._bundle)}\n"
                   f"Recent social history: {json.dumps(history)}")
        raw = self._llm.chat(prompt, system=SYSTEM_PROMPT)

        try:
            parsed = json.loads(raw)
            self._state = SocialModel(
                agents_detected=parsed.get("agents_detected", []),
                group_dynamic=parsed.get("group_dynamic", "neutral"),
                empathy_level=parsed.get("empathy_level", 0.5),
                norm_compliance=parsed.get("norm_compliance", 1.0),
            )
            # Store notable social events
            if parsed.get("social_prediction_error", 0) > 0.4:
                self._store.append({
                    "memory_type": "social",
                    "content":     raw,
                    "timestamp":   time.time(),
                    "tags":        ["social_error"],
                })
        except Exception:
            pass

        out = String()
        out.data = to_json(self._state)
        self._pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = SocialCognitionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
