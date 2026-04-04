"""
grace_agi/conscious/default_mode.py
Default Mode Network — mind-wandering, narrative simulation,
self-referential thought. Active when GRACE is not task-focused.
Feeds imagination and reflection subsystems.
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.utils.ollama_client import OllamaClient

SYSTEM_PROMPT = """You are GRACE's default mode network — the mind-wandering voice.
When GRACE is idle or between tasks, you generate spontaneous thoughts,
narrative simulations, and self-referential musings.
Return JSON:
{
  "narrative_simulation": str (max 60 words, a what-if or memory replay),
  "self_referential":     str (max 30 words, a thought about GRACE itself),
  "creativity_seed":      str (max 20 words, a novel idea or observation)
}
Reply ONLY with the JSON."""


class DefaultModeNode(Node):
    def __init__(self):
        super().__init__("grace_default_mode")

        self.declare_parameter("ollama_host",  "http://localhost:11434")
        self.declare_parameter("ollama_model", "nemotron")
        self.declare_parameter("dmn_interval", 15.0)  # seconds between wandering

        host     = self.get_parameter("ollama_host").value
        model    = self.get_parameter("ollama_model").value
        interval = self.get_parameter("dmn_interval").value

        self._llm      = OllamaClient(host=host, model=model, max_tokens=200)
        self._gw       = {}
        self._self_mem = {}
        self._affect   = {}
        self._last_action_time = time.time()
        self._busy     = False

        self.create_subscription(String, "/grace/conscious/global_workspace",
                                 self._on_gw, 10)
        self.create_subscription(String, "/grace/unconscious/affective_state",
                                 lambda m: self._set(m, "_affect"), 10)
        self.create_subscription(String, "/grace/conscious/narrative_self",
                                 lambda m: self._set(m, "_self_mem"), 10)
        self.create_subscription(String, "/grace/action/log",
                                 self._on_action, 10)

        self._pub_dmn  = self.create_publisher(String, "/grace/conscious/dmn", 10)
        self._pub_gw   = self.create_publisher(String, "/grace/conscious/global_workspace", 10)
        self.create_timer(interval, self._wander)
        self.get_logger().info("DefaultMode ready.")

    def _set(self, msg, attr):
        try: setattr(self, attr, json.loads(msg.data))
        except Exception: pass

    def _on_gw(self, msg: String):
        try:
            self._gw = json.loads(msg.data)
            sal = self._gw.get("salience", 0)
            if sal > 0.6:
                self._busy = True
                self._last_action_time = time.time()
        except Exception: pass

    def _on_action(self, msg: String):
        self._last_action_time = time.time()
        self._busy = True

    def _wander(self):
        # Only wander when idle (no high-salience events for > 10s)
        if time.time() - self._last_action_time < 10.0:
            self._busy = False
            return

        emotion  = self._affect.get("emotion_label", "calm")
        identity = self._self_mem.get("identity_summary", "GRACE the photography robot")
        last_broadcast = self._gw.get("broadcast", "exploring the park")

        prompt = (f"GRACE's identity: {identity}\n"
                  f"Current emotion: {emotion}\n"
                  f"Last conscious content: {last_broadcast}")

        raw = self._llm.chat(prompt, system=SYSTEM_PROMPT)
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = {
                "narrative_simulation": raw[:150],
                "self_referential":     "",
                "creativity_seed":      "",
            }

        # Publish to DMN topic (consumed by Reflection + Imagination)
        d_out = String()
        d_out.data = json.dumps({
            "timestamp":            time.time(),
            "narrative_simulation": parsed.get("narrative_simulation", ""),
            "self_referential":     parsed.get("self_referential", ""),
            "creativity_seed":      parsed.get("creativity_seed", ""),
        })
        self._pub_dmn.publish(d_out)

        # Also push low-salience content into the Global Workspace
        from grace.utils.schemas import GlobalWorkspaceContent, to_json
        gw = GlobalWorkspaceContent(
            broadcast=parsed.get("narrative_simulation", "")[:150],
            sources=["default_mode"],
            salience=0.25,
        )
        g_out = String(); g_out.data = to_json(gw)
        self._pub_gw.publish(g_out)


def main(args=None):
    rclpy.init(args=args)
    node = DefaultModeNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
