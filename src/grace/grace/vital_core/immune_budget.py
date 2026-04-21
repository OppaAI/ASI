"""
grace_agi/vital_core/immune_budget.py
Vital Core — Immune-Like Threat Budget
Accumulated Relational Threat · Social Pain
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.grace.utils.schemas import ImmuneBudget, to_json


class ImmuneBudgetNode(Node):
    def __init__(self):
        super().__init__("grace_immune_budget")

        # ── Parameters ────────────────────────────────────────────────────────
        self.declare_parameter("update_hz", 0.1)  # Slow accumulation tracking
        self.update_hz = self.get_parameter("update_hz").value

        # ── Internal State ───────────────────────────────────────────────────
        self._relational_threat_budget = 0.0  # 0=no threat  1=overwhelming
        self._social_pain_accumulation = 0.0  # Lifetime social pain exposure
        self._threat_decay_rate = 0.005       # Per hour threat reduction (forgiveness/time)
        self._social_pain_healing_rate = 0.002 # Per hour healing from positive interactions
        self._last_update = time.time()
        self._last_social_reset = time.time()  # For tracking recent social environment

        # ── Threat Accumulation Factors ─────────────────────────────────────
        self._rejection_sensitivity = 0.7     # How strongly rejection is felt
        self._betrayal_multiplier = 2.0       # Betrayal counts as 2x normal threat
        self._isolation_multiplier = 1.5      # Chronic isolation increases threat sensitivity
        self._positive_experience_buffer = 0.3 # Positive experiences buffer against threat

        # ── Subscribers (Inputs from social systems) ─────────────────────────
        # Social rejection/exclusion signals
        self.create_subscription(String, "/grace/social/rejection_signals",
                                 self._on_rejection, 10)
        # Interpersonal conflict and betrayal
        self.create_subscription(String, "/grace/social/betrayal_signals",
                                 self._on_betrayal, 10)
        # Chronic isolation/loneliness
        self.create_subscription(String, "/grace/social/isolation_signals",
                                 self._on_isolation, 10)
        # Positive social bonding and support
        self.create_subscription(String, "/grace/social/bonding_signals",
                                 self._on_positive_bonding, 10)
        # Social evaluation anxiety
        self.create_subscription(String, "/grace/social/evaluation_anxiety",
                                 self._on_evaluation_anxiety, 10)

        # ── Publishers (Outputs to other systems) ───────────────────────────
        self._pub = self.create_publisher(String, "/grace/vital/immune_budget", 10)
        self.create_timer(1.0 / self.update_hz, self._update_budget)
        self.get_logger().info("Immune-Like Threat Budget ready.")

    # ── Input Processing (Threat Accumulation) ─────────────────────────────
    def _on_rejection(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Social rejection creates threat sensitivity
            rejection_intensity = data.get("intensity", 0.0)  # 0-1
            personal_significance = data.get("personal_significance", 0.5)
            threat_increment = (rejection_intensity * self._rejection_sensitivity *
                              personal_significance * 0.1)
            self._relational_threat_budget += threat_increment
            self._social_pain_accumulation += threat_increment * 0.7  # Most rejection is painful
        except Exception as e:
            self.get_logger().warn(f"Failed to process rejection signal: {e}")

    def _on_betrayal(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Betrayal creates significant threat sensitivity
            betrayal_intensity = data.get("intensity", 0.0)  # 0-1
            relationship_value = data.get("relationship_value", 0.5)  # How valuable was relationship
            threat_increment = (betrayal_intensity * self._betrayal_multiplier *
                              relationship_value * 0.15)
            self._relational_threat_budget += threat_increment
            self._social_pain_accumulation += threat_increment  # Betrayal is deeply painful
        except Exception as e:
            self.get_logger().warn(f"Failed to process betrayal signal: {e}")

    def _on_isolation(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Chronic isolation increases threat sensitivity and baseline threat
            isolation_duration = data.get("duration_hours", 0.0)  # Hours since last connection
            isolation_severity = min(1.0, isolation_duration / 168.0)  # Normalize to week
            threat_increment = (isolation_severity * self._isolation_multiplier * 0.05)
            self._relational_threat_budget += threat_increment
            # Isolation also creates loneliness (social pain)
            self._social_pain_accumulation += threat_increment * 0.6
        except Exception as e:
            self.get_logger().warn(f"Failed to process isolation signal: {e}")

    def _on_positive_bonding(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Positive bonding experiences reduce threat sensitivity and heal social pain
            bonding_quality = data.get("quality", 0.0)  # 0-1
            relationship_depth = data.get("depth", 0.5)  # How deep the connection
            healing_amount = (bonding_quality * relationship_depth *
                            self._positive_experience_buffer * 0.08)
            # Healing reduces threat budget (but not below zero)
            self._relational_threat_budget = max(0.0,
                                               self._relational_threat_budget - healing_amount)
            # Positive experiences also heal social pain
            self._social_pain_accumulation = max(0.0,
                                               self._social_pain_accumulation - healing_amount * 0.5)
        except Exception as e:
            self.get_logger().warn(f"Failed to process positive bonding: {e}")

    def _on_evaluation_anxiety(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Social evaluation anxiety creates anticipatory threat
            anxiety_level = data.get("anxiety", 0.0)  # 0-1
            evaluative_importance = data.get("importance", 0.5)  # How important is evaluation
            threat_increment = (anxiety_level * evaluative_importance * 0.06)
            self._relational_threat_budget += threat_increment
            # Evaluation anxiety is also socially painful in anticipation
            self._social_pain_accumulation += threat_increment * 0.4
        except Exception as e:
            self.get_logger().warn(f"Failed to process evaluation anxiety: {e}")

    # ── Budget Dynamics Update ─────────────────────────────────────────────
    def _update_budget(self):
        now = time.time()
        dt = now - self._last_update
        self._last_update = now

        # Threat decay over time (natural healing, forgiveness, perspective)
        threat_decay = self._relational_threat_budget * self._threat_decay_rate * dt
        self._relational_threat_budget = max(0.0, self._relational_threat_budget - threat_decay)

        # Social pain healing (time heals wounds, but scars may remain)
        social_pain_healing = self._social_pain_accumulation * self._social_pain_healing_rate * dt
        self._social_pain_accumulation = max(0.0, self._social_pain_accumulation - social_pain_healing)

        # Isolation effect increases threat sensitivity when isolated
        # This would need tracking of recent social isolation - simplified here

        # Publish immune budget state
        immune_budget = ImmuneBudget(
            timestamp=now,
            relational_threat_budget=self._relational_threat_budget,
            social_pain_accumulation=self._social_pain_accumulation,
            threat_decay_rate=self._threat_decay_rate,
            social_pain_healing_rate=self._social_pain_healing_rate,
            threat_buffer=max(0.0, self._positive_experience_buffer -
                            self._relational_threat_budget * 0.5)
        )
        out = String()
        out.data = to_json(immune_budget)
        self._pub.publish(out)

        # Log when threat budget becomes concerning
        if self._relational_threat_budget > 0.7 and int(now) % 300 == 0:  # Every 5 minutes when high
            self.get_logger().warn(
                f"High Relational Threat: {self._relational_threat_budget:.2f} "
                f"(Social Pain: {self._social_pain_accumulation:.2f})"
            )


def main(args=None):
    rclpy.init(args=args)
    node = ImmuneBudgetNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()