"""
grace_agi/subconscious/procedural_memory.py
Skills, habits, and cognitive styles. Mostly rule-based — no LLM needed.
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.utils.memory_store import MemoryStore

DEFAULT_SKILLS = [
    {"skill": "navigate_to_waypoint", "proficiency": 0.85, "tags": ["navigation"]},
    {"skill": "avoid_obstacle",       "proficiency": 0.90, "tags": ["safety"]},
    {"skill": "photograph_subject",   "proficiency": 0.75, "tags": ["photography"]},
    {"skill": "greet_person",         "proficiency": 0.80, "tags": ["social"]},
    {"skill": "return_to_home",       "proficiency": 0.95, "tags": ["navigation"]},
    {"skill": "slam_mapping",         "proficiency": 0.80, "tags": ["navigation"]},
]


class ProceduralMemoryNode(Node):
    def __init__(self):
        super().__init__("grace_procedural_memory")
        self.declare_parameter("procedural_db", "/home/grace/memory/procedural.json")
        db_path = self.get_parameter("procedural_db").value
        self._store = MemoryStore(db_path, max_entries=200)

        if not self._store.all():
            for s in DEFAULT_SKILLS:
                s["memory_type"] = "procedural"
                self._store.append(s)

        self.create_subscription(String, "/grace/subconscious/procedural",
                                 self._on_write, 10)
        self.create_subscription(String, "/grace/dreaming/consolidation",
                                 self._on_consolidation, 10)

        self._pub = self.create_publisher(String, "/grace/subconscious/procedural_recall", 10)
        self.create_timer(10.0, self._broadcast_skills)
        self.get_logger().info("ProceduralMemory ready.")

    def _on_write(self, msg: String):
        try:
            entry = json.loads(msg.data)
            entry["memory_type"] = "procedural"
            self._store.append(entry)
        except Exception: pass

    def _on_consolidation(self, msg: String):
        # Consolidation can update skill proficiency
        pass

    def _broadcast_skills(self):
        skills = self._store.all()
        out = String()
        out.data = json.dumps({
            "memory_type": "procedural",
            "skills":      skills,
            "timestamp":   time.time(),
        })
        self._pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(ProceduralMemoryNode())
    rclpy.shutdown()
