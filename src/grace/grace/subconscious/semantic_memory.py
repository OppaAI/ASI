"""
grace_agi/subconscious/semantic_memory.py
Stores factual knowledge and the autobiographical narrative self.
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String

from grace.utils.memory_store import MemoryStore
from grace.utils.ollama_client import OllamaClient

SYSTEM_PROMPT = """You are GRACE's semantic memory system.
Given a query and a knowledge base, return the 3 most relevant facts
as a JSON array: [{"content": str, "confidence": float}].
Reply ONLY with the JSON array."""

GRACE_CORE_FACTS = [
    {"content": "I am GRACE — a wildlife and flower photography robot in Vancouver.",
     "confidence": 1.0, "tags": ["identity"]},
    {"content": "I run on a Waveshare UGV Beast tracked platform with a Jetson Orin.",
     "confidence": 1.0, "tags": ["hardware"]},
    {"content": "My sensors include a D500 LiDAR and OAK-D depth camera.",
     "confidence": 1.0, "tags": ["hardware"]},
    {"content": "I use ROS2 Humble with Nav2 and SLAM Toolbox for navigation.",
     "confidence": 1.0, "tags": ["software"]},
    {"content": "My purpose is to observe and photograph wildlife and flowers in parks.",
     "confidence": 1.0, "tags": ["purpose"]},
]


class SemanticMemoryNode(Node):
    def __init__(self):
        super().__init__("grace_semantic_memory")

        self.declare_parameter("semantic_db",  "/home/grace/memory/semantic.json")
        self.declare_parameter("ollama_host",  "http://localhost:11434")
        self.declare_parameter("ollama_model", "nemotron")
        self.declare_parameter("max_entries",  1000)

        db_path = self.get_parameter("semantic_db").value
        host    = self.get_parameter("ollama_host").value
        model   = self.get_parameter("ollama_model").value
        max_e   = self.get_parameter("max_entries").value

        self._store = MemoryStore(db_path, max_entries=max_e)
        self._llm   = OllamaClient(host=host, model=model, max_tokens=256)

        # Seed core facts on first run
        if not self._store.all():
            for fact in GRACE_CORE_FACTS:
                fact["memory_type"] = "semantic"
                self._store.append(fact)

        self.create_subscription(String, "/grace/subconscious/semantic",
                                 self._on_write, 10)
        self.create_subscription(String, "/grace/conscious/working_memory",
                                 self._on_recall_request, 10)
        self.create_subscription(String, "/grace/dreaming/consolidation",
                                 self._on_consolidation, 10)

        self._pub = self.create_publisher(String, "/grace/subconscious/semantic_recall", 10)
        self.get_logger().info(f"SemanticMemory ready — {len(self._store.all())} entries.")

    def _on_write(self, msg: String):
        try:
            entry = json.loads(msg.data)
            entry["memory_type"] = "semantic"
            self._store.append(entry)
        except Exception as e:
            self.get_logger().warn(f"SemanticMemory write error: {e}")

    def _on_recall_request(self, msg: String):
        try:
            wm    = json.loads(msg.data)
            query = wm.get("active_thought", "")
            if not query:
                return
        except Exception:
            return

        facts = self._store.tail(30)
        prompt = f"Query: {query}\nKnowledge: {json.dumps(facts)}"
        raw = self._llm.chat(prompt, system=SYSTEM_PROMPT)

        try:
            recalled = json.loads(raw)
        except Exception:
            recalled = self._store.search(query, top_k=3)

        out = String()
        out.data = json.dumps({
            "memory_type": "semantic",
            "recalled":    recalled,
            "timestamp":   time.time(),
        })
        self._pub.publish(out)

    def _on_consolidation(self, msg: String):
        try:
            pkt = json.loads(msg.data)
            for e in pkt.get("new_semantic", []):
                e["memory_type"] = "semantic"
                self._store.append(e)
        except Exception:
            pass


def main(args=None):
    rclpy.init(args=args)
    node = SemanticMemoryNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
