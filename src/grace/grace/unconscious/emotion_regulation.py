"""
grace_agi/unconscious/emotion_regulation.py
Unconscious Layer — Emotion Regulation Strategies
Suppression · Reappraisal · Rumination
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.grace.utils.schemas import EmotionRegulationState, to_json


class EmotionRegulationNode(Node):
    def __init__(self):
        super().__init__("grace_emotion_regulation")

        # ── Parameters ────────────────────────────────────────────────────────
        self.declare_parameter("update_hz", 2.0)  # Fast emotion regulation
        self.update_hz = self.get_parameter("update_hz").value

        # ── Internal State (Regulation Strategy Usage) ───────────────────────
        # Proportion of time spent in each strategy (0-1, should sum to <= 1)
        self._suppression = 0.2    # Expressive suppression
        self._reappraisal = 0.5    # Cognitive reappraisal
        self._rumination = 0.1     # Passive repetitive focus on distress
        self._acceptance = 0.2     # Acceptance/mindfulness (healthy alternative)
        self._last_update = time.time()

        # ── Strategy Effectiveness Parameters ────────────────────────────────
        self._suppression_cost = 0.3     # Cognitive/emotional cost of suppression
        self._reappraisal_benefit = 0.4  # Emotional benefit of reappraisal
        self._rumination_cost = 0.5      # Emotional cost of rumination
        self._acceptance_benefit = 0.3   # Emotional benefit of acceptance

        # ── Subscribers (Inputs from other systems) ─────────────────────────
        # Affective state to regulate
        self.create_subscription(String, "/grace/unconscious/affective_state",
                                 self._on_affective_state, 10)
        # Pain signals triggering regulation needs
        self.create_subscription(String, "/grace/vital/pain_signal",
                                 self._on_pain_signal, 10)
        # Social threats increasing regulation demand
        self.create_subscription(String, "/grace/vital/immune_budget",
                                 self._on_threat_budget, 10)
        # Cognitive resources available for regulation
        self.create_subscription(String, "/grace/vital/metabolic_resource",
                                 self._on_metabolic_state, 10)
        # Executive control efforts
        self.create_subscription(String, "/grace/conscious/executive_plan",
                                 self._on_executive_control, 10)

        # ── Publishers (Outputs to other systems) ───────────────────────────
        self._pub = self.create_publisher(String, "/grace/unconscious/emotion_regulation", 10)
        self.create_timer(1.0 / self.update_hz, self._update_regulation)
        self.get_logger().info("Emotion Regulation Strategies ready.")

    # ── Input Processing ─────────────────────────────────────────────────────
    def _on_affective_state(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Current emotional state influences regulation strategy selection
            arousal = data.get("arousal", 0.3)      # 0-1
            valence = data.get("valence", 0.5)      # 0-1 (0=negative, 1=positive)

            # High arousal + negative valence increases regulation need
            emotional_distress = arousal * (1.0 - valence)

            # Shift strategy mix based on distress and available resources
            self._shift_strategy_mix(emotional_distress)
        except Exception as e:
            self.get_logger().warn(f"Failed to process affective state: {e}")

    def _on_pain_signal(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Psychological pain increases need for emotion regulation
            pain_intensity = data.get("pain_intensity", 0.0)
            # Pain increases rumination tendency and suppression
            rumination_boost = pain_intensity * 0.3
            suppression_boost = pain_intensity * 0.2

            self._rumination = min(0.8, self._rumination + rumination_boost)
            self._suppression = min(0.6, self._suppression + suppression_boost)
            # Compensatory decrease in healthy strategies
            total_increase = rumination_boost + suppression_boost
            self._reappraisal = max(0.1, self._reappraisal - total_increase * 0.4)
            self._acceptance = max(0.1, self._acceptance - total_increase * 0.6)
        except Exception as e:
            self.get_logger().warn(f"Failed to process pain signal: {e}")

    def _on_threat_budget(self, msg: String):
        try:
            data = json.loads(msg.data)
            # High threat budget increases emotion regulation needs
            threat_level = data.get("relational_threat_budget", 0.0)
            # Chronic threat increases suppression and rumination
            threat_effect = threat_level * 0.4
            self._suppression = min(0.7, self._suppression + threat_effect * 0.6)
            self._rumination = min(0.7, self._rumination + threat_effect * 0.4)
            # Healthy strategies decrease under chronic threat
            self._reappraisal = max(0.1, self._reappraisal - threat_effect * 0.5)
            self._acceptance = max(0.1, self._acceptance - threat_effect * 0.5)
        except Exception as e:
            self.get_logger().warn(f"Failed to process threat budget: {e}")

    def _on_metabolic_state(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Low cognitive resources impair effortful regulation (reappraisal)
            glucose = data.get("glucose_equivalent", 1.0)
            if glucose < 0.5:  # Low fuel
                # Shift from effortful reappraisal to automatic suppression
                shift_amount = (0.5 - glucose) * 0.3
                self._suppression = min(0.7, self._suppression + shift_amount)
                self._reappraisal = max(0.1, self._reappraisal - shift_amount)
            # Acceptance less affected by metabolic state
        except Exception as e:
            self.get_logger().warn(f"Failed to process metabolic state: {e}")

    def _on_executive_control(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Executive control efforts support healthy regulation strategies
            control_effort = data.get("priority", 0.5) * len(data.get("steps", [])) * 0.1
            control_effort = min(1.0, control_effort)

            # Executive control boosts reappraisal and acceptance
            boost = control_effort * 0.2
            self._reappraisal = min(0.8, self._reappraisal + boost)
            self._acceptance = min(0.6, self._acceptance + boost * 0.5)
            # Reduces reliance on suppression and rumination
            reduction = boost * 0.3
            self._suppression = max(0.1, self._suppression - reduction)
            self._rumination = max(0.05, self._rumination - reduction * 0.5)
        except Exception as e:
            self.get_logger().warn(f"Failed to process executive control: {e}")

    def _shift_strategy_mix(self, distress_level: float):
        """Shift strategy mix based on emotional distress level"""
        # High distress increases use of all regulation strategies
        # but with bias toward available resources and tendencies
        total_regulation_need = min(1.0, 0.3 + distress_level * 0.5)

        # Distress increases rumination (maladaptive) and suppression
        rumination_increase = distress_level * 0.4
        suppression_increase = distress_level * 0.3

        self._rumination = min(0.8, self._rumination + rumination_increase)
        self._suppression = min(0.7, self._suppression + suppression_increase)

        # Compensatory shifts - under high distress, healthy strategies may decrease
        # unless resources are available (handled in other inputs)
        total_increase = rumination_increase + suppression_increase
        if self._reappraisal + self._acceptance > total_increase * 0.5:
            # Reduce healthy strategies proportionally
            reduction_factor = total_increase * 0.3
            self._reappraisal = max(0.1, self._reappraisal - reduction_factor)
            self._acceptance = max(0.1, self._acceptance - reduction_factor * 0.7)

    # ── Regulation Dynamics Update ───────────────────────────────────────────
    def _update_regulation(self):
        now = time.time()
        dt = now - self._last_update
        self._last_update = now

        # Normalize strategy proportions to prevent exceeding 1.0
        total = self._suppression + self._reappraisal + self._rumination + self._acceptance
        if total > 1.0:
            # Scale down proportionally
            scale = 1.0 / total
            self._suppression *= scale
            self._reappraisal *= scale
            self._rumination *= scale
            self._acceptance *= scale

        # Calculate net emotional impact of regulation strategies
        net_emotional_impact = (
            -self._suppression * self._suppression_cost +  # Suppression has cost
            self._reappraisal * self._reappraisal_benefit +  # Reappraisal has benefit
            -self._rumination * self._rumination_cost +    # Rumination has cost
            self._acceptance * self._acceptance_benefit    # Acceptance has benefit
        )

        # Publish regulation state
        regulation_state = EmotionRegulationState(
            timestamp=now,
            suppression=self._suppression,
            reappraisal=self._reappraisal,
            rumination=self._rumination,
            acceptance=self._acceptance,
            net_emotional_impact=net_emotional_impact,
            strategy_entropy=self._calculate_entropy()
        )
        out = String()
        out.data = to_json(regulation_state)
        self._pub.publish(out)

        # Log regulation profile occasionally
        if int(now) % 10 == 0:  # Every 10 seconds
            self.get_logger().info(
                f"Emotion Reg - Supp:{self._suppression:.2f} "
                f"Reapp:{self._reappraisal:.2f} "
                f"Rum:{self._rumination:.2f} "
                f"Accept:{self._acceptance:.2f} "
                f"NetImpact:{net_emotional_impact:.2f}"
            )

    def _calculate_entropy(self) -> float:
        """Calculate entropy of strategy distribution (higher = more diverse)"""
        import math
        strategies = [self._suppression, self._reappraisal, self._rumination, self._acceptance]
        # Normalize to probabilities
        total = sum(strategies)
        if total == 0:
            return 0.0
        probs = [s/total for s in strategies]
        # Shannon entropy
        entropy = -sum(p * math.log(p) for p in probs if p > 0)
        return entropy


def main(args=None):
    rclpy.init(args=args)
    node = EmotionRegulationNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()