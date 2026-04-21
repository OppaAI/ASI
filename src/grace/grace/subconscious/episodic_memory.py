"""
grace_agi/subconscious/episodic_memory.py
Stores and retrieves personal experiences tagged with emotion and context.
Accepts writes from ImplicitMemory and WorkingMemory.
Answers recall queries for the MemoryCoordinator.
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String

from grace.grace.utils.schemas import MemoryEntry, to_json
from grace.grace.utils.memory_store import MemoryStore
from grace.grace.utils.ollama_client import OllamaClient

SYSTEM_PROMPT = """You are GRACE's episodic memory system.
Given a query and a list of memory entries, return the 3 most relevant memories
as a JSON array of objects: [{"content": str, "emotional_tag": float, "timestamp": float}].
Reply ONLY with the JSON array."""


class EpisodicMemoryNode(Node):
    def __init__(self):
        super().__init__("grace_episodic_memory")

        self.declare_parameter("episodic_db",   "/home/grace/memory/episodic.json")
        self.declare_parameter("ollama_host",   "http://localhost:11434")
        self.declare_parameter("ollama_model",  "nemotron")
        self.declare_parameter("max_entries",   500)

        db_path  = self.get_parameter("episodic_db").value
        host     = self.get_parameter("ollama_host").value
        model    = self.get_parameter("ollama_model").value
        max_ent  = self.get_parameter("max_entries").value

        self._store  = MemoryStore(db_path, max_entries=max_ent)
        self._llm    = OllamaClient(host=host, model=model, max_tokens=256)
        self._affect = {}

        # Track current affective state for emotional tagging
        self.create_subscription(String, "/grace/unconscious/affective_state",
                                 lambda m: self._set(m, "_affect"), 10)

        # Writes from implicit memory and working memory
        self.create_subscription(String, "/grace/subconscious/episodic",
                                 self._on_write, 10)

        # Recall requests from memory coordinator
        self.create_subscription(String, "/grace/conscious/working_memory",
                                 self._on_recall_request, 10)

        # Consolidation updates
        self.create_subscription(String, "/grace/dreaming/consolidation",
                                 self._on_consolidation, 10)

        self._pub = self.create_publisher(String, "/grace/subconscious/episodic_recall", 10)
        self.get_logger().info(f"EpisodicMemory ready — {len(self._store.all())} entries loaded.")

    def _set(self, msg, attr):
        try: setattr(self, attr, json.loads(msg.data))
        except Exception: pass

    def _on_write(self, msg: String):
        try:
            entry = json.loads(msg.data)
            entry["emotional_tag"] = self._affect.get("valence", 0.5)
            entry["memory_type"]   = "episodic"
            self._store.append(entry)
        except Exception as e:
            self.get_logger().warn(f"EpisodicMemory write error: {e}")

    def _on_recall_request(self, msg: String):
        try:
            wm = json.loads(msg.data)
            query = wm.get("active_thought", "")
            if not query:
                return
        except Exception:
            return

        recent = self._store.tail(20)
        if not recent:
            return

        prompt = f"Query: {query}\nMemories: {json.dumps(recent)}"
        raw = self._llm.chat(prompt, system=SYSTEM_PROMPT)

        try:
            recalled = json.loads(raw)
        except Exception:
            # Fallback: plain substring search
            recalled = self._store.search(query, top_k=3)

        out = String()
        out.data = json.dumps({
            "memory_type": "episodic",
            "recalled":    recalled,
            "timestamp":   time.time(),
        })
        self._pub.publish(out)

    def _on_consolidation(self, msg: String):
        try:
            pkt = json.loads(msg.data)
            for e in pkt.get("new_episodic", []):
                e["memory_type"] = "episodic"
                self._store.append(e)
        except Exception:
            pass


def main(args=None):
    rclpy.init(args=args)
    node = EpisodicMemoryNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
