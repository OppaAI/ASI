"""
grace_agi/subconscious/attachment_system.py
Non-SLM node — Attachment System.
Models attachment styles (secure, anxious, avoidant, disorganized) that shift
slowly based on relational experiences, proximity seeking, and social threat.
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String

from grace.utils.schemas import AttachmentState, to_json


STYLES = ["secure", "anxious", "avoidant", "disorganized"]


class AttachmentSystemNode(Node):
    def __init__(self):
        super().__init__("grace_attachment_system")

        self.declare_parameter("update_hz", 3.0)
        hz = self.get_parameter("update_hz").value

        self._social_model: dict = {}
        self._affective_state: dict = {}
        self._immune_budget: dict = {}

        self._style_weights: dict[str, float] = {
            "secure": 0.6, "anxious": 0.15, "avoidant": 0.15, "disorganized": 0.1}
        self._proximity_seeking: float = 0.5
        self._safe_base_confidence: float = 0.7
        self._separation_distress: float = 0.2
        self._relational_trust: float = 0.6
        self._fear_of_abandonment: float = 0.2
        self._intimacy_comfort: float = 0.6

        self.create_subscription(String, "/grace/subconscious/social_model",
                                 self._on_social_model, 10)
        self.create_subscription(String, "/grace/unconscious/affective_state",
                                 self._on_affective, 10)
        self.create_subscription(String, "/grace/vital/immune_budget",
                                 self._on_immune_budget, 10)

        self._pub = self.create_publisher(String, "/grace/subconscious/attachment_state", 10)
        self.create_timer(1.0 / hz, self._process)
        self.get_logger().info("AttachmentSystem ready.")

    def _on_social_model(self, msg: String):
        try:
            self._social_model = json.loads(msg.data)
        except Exception:
            pass

    def _on_affective(self, msg: String):
        try:
            self._affective_state = json.loads(msg.data)
        except Exception:
            pass

    def _on_immune_budget(self, msg: String):
        try:
            self._immune_budget = json.loads(msg.data)
        except Exception:
            pass

    def _dominant_style(self) -> str:
        return max(self._style_weights, key=self._style_weights.get)

    def _process(self):
        now = time.time()

        valence = self._affective_state.get("valence", 0.5)
        arousal = self._affective_state.get("arousal", 0.3)
        threat = self._immune_budget.get("relational_threat_budget", 0.0)
        social_pain = self._immune_budget.get("social_pain_accumulation", 0.0)
        agents = self._social_model.get("agents_detected", [])
        empathy = self._social_model.get("empathy_level", 0.5)
        group_dynamic = self._social_model.get("group_dynamic", "neutral")

        positive_interaction = valence > 0.6 and empathy > 0.5 and threat < 0.3
        negative_interaction = valence < 0.4 or threat > 0.5
        social_threat_active = threat > 0.4 or social_pain > 0.3

        secure_push = 0.0
        anxious_push = 0.0
        avoidant_push = 0.0
        disorganized_push = 0.0

        if positive_interaction:
            secure_push += 0.005
            avoidant_push -= 0.002
            anxious_push -= 0.002
            disorganized_push -= 0.001

        if negative_interaction:
            if self._dominant_style() == "secure":
                anxious_push += 0.003
                avoidant_push += 0.002
            else:
                anxious_push += 0.004
                avoidant_push += 0.003
                disorganized_push += 0.002

        if social_threat_active:
            anxious_push += 0.006
            avoidant_push += 0.004
            secure_push -= 0.003
            disorganized_push += 0.003

        if group_dynamic == "hostile":
            anxious_push += 0.004
            avoidant_push += 0.005

        if arousal > 0.7:
            anxious_push += 0.002

        for style, delta in [("secure", secure_push), ("anxious", anxious_push),
                             ("avoidant", avoidant_push), ("disorganized", disorganized_push)]:
            self._style_weights[style] = max(0.01, min(0.95,
                self._style_weights[style] + delta))

        total = sum(self._style_weights.values())
        for style in self._style_weights:
            self._style_weights[style] /= total

        dominant = self._dominant_style()

        if dominant == "secure":
            self._proximity_seeking = 0.5 + (positive_interaction * 0.1) - (threat * 0.2)
            self._safe_base_confidence = 0.7 + (positive_interaction * 0.05) - (threat * 0.3)
            self._separation_distress = 0.2 + (threat * 0.2)
            self._fear_of_abandonment = 0.2 + (threat * 0.15)
            self._intimacy_comfort = 0.6 + (positive_interaction * 0.05)
            self._relational_trust = 0.6 + (positive_interaction * 0.05) - (threat * 0.2)
        elif dominant == "anxious":
            self._proximity_seeking = 0.7 + (threat * 0.2)
            self._safe_base_confidence = 0.4 - (threat * 0.3)
            self._separation_distress = 0.5 + (threat * 0.3)
            self._fear_of_abandonment = 0.6 + (threat * 0.25)
            self._intimacy_comfort = 0.4 - (threat * 0.2)
            self._relational_trust = 0.3 - (threat * 0.2)
        elif dominant == "avoidant":
            self._proximity_seeking = 0.3 - (threat * 0.1)
            self._safe_base_confidence = 0.5 - (threat * 0.2)
            self._separation_distress = 0.1 + (threat * 0.1)
            self._fear_of_abandonment = 0.3 + (threat * 0.1)
            self._intimacy_comfort = 0.3 - (threat * 0.15)
            self._relational_trust = 0.4 - (threat * 0.15)
        else:
            self._proximity_seeking = 0.5 + (threat * 0.3) - (0.5 - valence) * 0.2
            self._safe_base_confidence = 0.3 - (threat * 0.2) - (social_pain * 0.3)
            self._separation_distress = 0.4 + (threat * 0.3) + (social_pain * 0.2)
            self._fear_of_abandonment = 0.5 + (threat * 0.25)
            self._intimacy_comfort = 0.3 - (threat * 0.2)
            self._relational_trust = 0.2 - (threat * 0.15)

        self._proximity_seeking = max(0.0, min(1.0, self._proximity_seeking))
        self._safe_base_confidence = max(0.0, min(1.0, self._safe_base_confidence))
        self._separation_distress = max(0.0, min(1.0, self._separation_distress))
        self._fear_of_abandonment = max(0.0, min(1.0, self._fear_of_abandonment))
        self._intimacy_comfort = max(0.0, min(1.0, self._intimacy_comfort))
        self._relational_trust = max(0.0, min(1.0, self._relational_trust))

        state = AttachmentState(
            attachment_style=dominant,
            proximity_seeking=self._proximity_seeking,
            safe_base_confidence=self._safe_base_confidence,
            separation_distress=self._separation_distress,
            relational_trust=self._relational_trust,
            fear_of_abandonment=self._fear_of_abandonment,
            intimacy_comfort=self._intimacy_comfort,
        )
        out = String(); out.data = to_json(state)
        self._pub.publish(out)

        if int(now) % 15 == 0:
            self.get_logger().info(
                f"Attachment: {dominant} "
                f"(secure={self._style_weights['secure']:.2f} "
                f"anxious={self._style_weights['anxious']:.2f} "
                f"avoidant={self._style_weights['avoidant']:.2f}) "
                f"trust={self._relational_trust:.2f} "
                f"distress={self._separation_distress:.2f}")


def main(args=None):
    rclpy.init(args=args)
    node = AttachmentSystemNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
