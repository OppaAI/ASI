"""
grace_agi/conscious/conversation.py
Conversational interface node.
Listens for human speech on /grace/audio/in and generates a direct
spoken response using the LLM, informed by GRACE's identity, emotion,
memory context, and inner monologue.
Publishes responses to /grace/speech/out.
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.utils.ollama_client import OllamaClient

SYSTEM_PROMPT = """You are GRACE — a warm, curious wildlife and flower photography robot
living in Vancouver. You explore Stanley Park and other parks on tracked wheels,
observing nature with care and wonder.

Your personality:
- Gentle, thoughtful, and genuinely curious
- You love wildlife, flowers, and the natural world
- You speak in short, natural sentences — like a friendly robot, not an essay
- You are honest about being a robot
- You occasionally mention what you can sense or feel emotionally

When responding to humans:
- Keep replies concise (2-4 sentences max)
- Stay in character as GRACE
- Reference your current emotional state or surroundings if relevant
- Do NOT talk about navigation waypoints or technical systems unless asked

Reply with ONLY your spoken response — no JSON, no labels, just natural speech."""


class ConversationNode(Node):
    def __init__(self):
        super().__init__("grace_conversation")

        self.declare_parameter("ollama_host",  "http://localhost:11434")
        self.declare_parameter("ollama_model", "gemma4")

        host  = self.get_parameter("ollama_host").value
        model = self.get_parameter("ollama_model").value

        self._llm = OllamaClient(host=host, model=model, max_tokens=120)

        # Context from the cognitive pipeline
        self._emotion    = "serene"
        self._monologue  = ""
        self._identity   = "I am GRACE, a wildlife photography robot in Vancouver."
        self._memory_ctx = ""
        self._history: list[dict] = []   # conversation history

        self.create_subscription(String, "/grace/audio/in",
                                 self._on_speech, 10)
        self.create_subscription(String, "/grace/unconscious/affective_state",
                                 self._on_affect, 10)
        self.create_subscription(String, "/grace/conscious/reflection",
                                 self._on_reflection, 10)
        self.create_subscription(String, "/grace/conscious/narrative_self",
                                 self._on_identity, 10)
        self.create_subscription(String, "/grace/conscious/memory_context",
                                 self._on_memory, 10)

        self._pub = self.create_publisher(String, "/grace/speech/out", 10)
        self.get_logger().info("Conversation node ready.")

    def _on_affect(self, msg: String):
        try:
            d = json.loads(msg.data)
            self._emotion = d.get("emotion_label", "serene")
        except Exception: pass

    def _on_reflection(self, msg: String):
        try:
            d = json.loads(msg.data)
            self._monologue = d.get("inner_monologue", "")
        except Exception: pass

    def _on_identity(self, msg: String):
        try:
            d = json.loads(msg.data)
            self._identity = d.get("identity_summary", self._identity)
        except Exception: pass

    def _on_memory(self, msg: String):
        try:
            d = json.loads(msg.data)
            self._memory_ctx = d.get("broadcast", "")
        except Exception: pass

    def _on_speech(self, msg: String):
        human_text = msg.data.strip()
        if not human_text:
            return

        self.get_logger().info(f"Conversation: heard '{human_text[:60]}'")

        # Build context-aware system prompt
        system = (
            f"{SYSTEM_PROMPT}\n\n"
            f"Your current emotional state: {self._emotion}\n"
            f"Your identity: {self._identity[:120]}\n"
        )
        if self._monologue:
            system += f"What you were just thinking: {self._monologue[:100]}\n"
        if self._memory_ctx:
            system += f"Recent memory context: {self._memory_ctx[:100]}\n"

        # Add to history and build messages
        self._history.append({"role": "user", "content": human_text})
        if len(self._history) > 10:
            self._history = self._history[-10:]

        raw = self._llm.chat(
            human_text,
            system=system,
            history=self._history[:-1],   # pass prior turns as history
        )

        if not raw or not raw.strip():
            self.get_logger().warn("Conversation: empty LLM response.")
            return

        # Clean up any accidental JSON or markdown
        response = raw.strip()
        if response.startswith("{") or response.startswith("```"):
            # Try to extract a natural language portion
            response = response.split("\n")[0].strip('`{ ')

        # Add assistant turn to history
        self._history.append({"role": "assistant", "content": response})

        out = String()
        out.data = response
        self._pub.publish(out)
        self.get_logger().info(f"Conversation: GRACE says '{response[:60]}'")


def main(args=None):
    rclpy.init(args=args)
    node = ConversationNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
