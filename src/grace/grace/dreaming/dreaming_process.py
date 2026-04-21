"""
grace_agi/dreaming/dreaming_process.py
Dreaming Process — offline emotional replay and predictive recombination.
Triggered by the consolidation timer or an explicit /grace/dreaming/trigger message.
Pulls from all memory systems, replays emotionally significant episodes,
and feeds the Imagination simulator.
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String, Bool

from grace.grace.utils.memory_store import MemoryStore
from grace.grace.utils.ollama_client import OllamaClient

SYSTEM_PROMPT = """You are GRACE's dreaming process — offline emotional replay.
Given a set of recent memories across different types, generate a dream sequence:
a recombination that replays emotionally significant events, explores novel
configurations, and surfaces latent patterns.
Return JSON:
{
  "dream_narrative":      str (max 120 words, surreal but grounded),
  "replayed_memories":    [str],
  "novel_combinations":   [str],
  "emotional_tone":       str,
  "salience_peaks":       [str]
}
Reply ONLY with the JSON."""


class DreamingProcessNode(Node):
    def __init__(self):
        super().__init__("grace_dreaming_process")

        self.declare_parameter("episodic_db",   "/home/grace/memory/episodic.json")
        self.declare_parameter("semantic_db",   "/home/grace/memory/semantic.json")
        self.declare_parameter("social_db",     "/home/grace/memory/social.json")
        self.declare_parameter("ollama_host",   "http://localhost:11434")
        self.declare_parameter("ollama_model",  "nemotron")
        self.declare_parameter("dreaming_interval", 300.0)

        self._store_e = MemoryStore(self.get_parameter("episodic_db").value,  500)
        self._store_s = MemoryStore(self.get_parameter("semantic_db").value, 1000)
        self._store_o = MemoryStore(self.get_parameter("social_db").value,    200)

        host  = self.get_parameter("ollama_host").value
        model = self.get_parameter("ollama_model").value
        interval = self.get_parameter("dreaming_interval").value

        self._llm = OllamaClient(host=host, model=model, max_tokens=400)

        self.create_subscription(String, "/grace/dreaming/trigger",
                                 self._on_trigger, 10)

        self._pub = self.create_publisher(String, "/grace/dreaming/dream_content", 10)

        # Automatic periodic dreaming
        self.create_timer(interval, self._dream)
        self.get_logger().info(
            f"DreamingProcess ready — dreaming every {interval:.0f}s.")

    def _on_trigger(self, msg: String):
        self.get_logger().info("DreamingProcess: manual trigger received.")
        self._dream()

    def _dream(self):
        self.get_logger().info("DreamingProcess: entering dream cycle...")

        # Sample from all memory systems
        episodic  = self._store_e.tail(10)
        semantic  = self._store_s.tail(5)
        social    = self._store_o.tail(5)

        memories_bundle = {
            "episodic":  episodic,
            "semantic":  semantic,
            "social":    social,
        }

        raw = self._llm.chat(
            f"Memories: {json.dumps(memories_bundle)}",
            system=SYSTEM_PROMPT)

        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = {
                "dream_narrative":    raw[:300],
                "replayed_memories":  [],
                "novel_combinations": [],
                "emotional_tone":     "neutral",
                "salience_peaks":     [],
            }

        parsed["timestamp"] = time.time()
        out = String(); out.data = json.dumps(parsed)
        self._pub.publish(out)
        self.get_logger().info(
            f"DreamingProcess: dream complete — tone: {parsed.get('emotional_tone')}")


def main(args=None):
    rclpy.init(args=args)
    node = DreamingProcessNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
