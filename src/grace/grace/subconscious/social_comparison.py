"""
grace_agi/subconscious/social_comparison.py
Subconscious Layer — Social Comparison Engine
Social Ranking · Envy · Pride · Schadenfreude
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.grace.utils.schemas import SocialComparisonState, to_json


class SocialComparisonNode(Node):
    def __init__(self):
        super().__init__("grace_social_comparison")

        # ── Parameters ────────────────────────────────────────────────────────
        self.declare_parameter("update_hz", 0.2)  # Updates every 5 seconds
        self.update_hz = self.get_parameter("update_hz").value

        # ── Internal State ───────────────────────────────────────────────────
        self._comparison_direction = 0.0       # -1=worse than others  0=same  1=better than others
        self._comparison_importance = 0.5      # 0=not important  1=extremely important
        self._social_ranking = 0.5             # 0=lowest rank  1=highest rank in group
        self._envy_level = 0.1                 # 0=no envy  1=intense envy
        self._pride_level = 0.6                # 0=no pride  1=excessive pride
        self._schadenfreude = 0.05             # 0=no schadenfreude  1=high schadenfreude
        self._competitiveness = 0.4            # 0=non-competitive  1=highly competitive
        self._conformity_pressure = 0.3        # 0=no pressure  1=high pressure to conform
        self._authenticity = 0.7               # 0=inauthentic  1=completely authentic
        self._last_update = time.time()

        # ── Social Comparison Parameters ───────────────────────────────────
        self._decay_rate = 0.01                # Natural decay of comparison effects
        self._learning_rate = 0.02             # Learning from social comparisons
        self._empathy_factor = 0.3             # How empathy reduces negative comparisons
        self._self_esteem_influence = 0.4      # How self-esteem affects comparison sensitivity
        self._status_anxiety = 0.2             # Anxiety about social status

        # ── Subscribers (Inputs from other systems) ─────────────────────────
        # Social context information
        self.create_subscription(String, "/grace/perception/social_context",
                                 self._on_social_context, 10)
        # Performance feedback from achievement systems
        self.create_subscription(String, "/grace/achievement/performance_feedback",
                                 self._on_performance_feedback, 10)
        # Social feedback from interactions
        self.create_subscription(String, "/grace/social/feedback_received",
                                 self._on_social_feedback, 10)
        # Achievement notifications from others
        self.create_subscription(String, "/grace/social/others_achievements",
                                 self._on_others_achievements, 10)
        # Self-esteem from self-evaluation systems
        self.create_subscription(String, "/grace/self/esteem_update",
                                 self._on_self_esteem_update, 10)

        # ── Publishers (Outputs to other systems) ───────────────────────────
        self._pub = self.create_publisher(String, "/grace/subconscious/social_comparison_state", 10)
        self.create_timer(1.0 / self.update_hz, self._update_social_comparison)
        self.get_logger().info("Social Comparison Engine ready.")

    # ── Input Processing ─────────────────────────────────────────────────────
    def _on_social_context(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Social context provides baseline for comparisons
            group_size = data.get("group_size", 1)              # Number of people in context
            group_competence = data.get("group_competence", 0.5) # Average competence of group
            social_dominance = data.get("social_dominance", 0.5) # Hierarchy in group

            # Update social ranking based on group context
            if group_size > 1:
                # Larger groups provide more comparison opportunities
                self._social_ranking = group_competence * (0.5 + social_dominance * 0.5)
                self._social_ranking = max(0.0, min(1.0, self._social_ranking))

            # Group competence affects comparison importance
            self._comparison_importance = min(1.0, 0.3 + group_competence * 0.5)

        except Exception as e:
            self.get_logger().warn(f"Failed to process social context: {e}")

    def _on_performance_feedback(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Performance feedback affects self-assessment and social comparison
            performance_score = data.get("score", 0.5)      # 0=poor  1=excellent
            feedback_credibility = data.get("credibility", 0.5) # Trustworthiness of feedback
            domain_relevance = data.get("relevance", 0.5)   # Relevance to current goals

            # Update self-assessment (affects comparison direction)
            self_assessment = performance_score * feedback_credibility * domain_relevance
            # Convert to -1 to 1 range for comparison direction
            self._comparison_direction = (self_assessment - 0.5) * 2.0
            self._comparison_direction = max(-1.0, min(1.0, self._comparison_direction))

            # High performance with credible feedback increases pride
            if performance_score > 0.6 and feedback_credibility > 0.6:
                pride_boost = (performance_score - 0.6) * feedback_credibility * 0.3
                self._pride_level = min(1.0, self._pride_level + pride_boost)
                # Pride reduces envy
                envy_reduction = pride_boost * 0.4
                self._envy_level = max(0.0, self._envy_level - envy_reduction)

            # Low performance increases envy if credibility is high
            if performance_score < 0.4 and feedback_credibility > 0.6:
                envy_boost = (0.4 - performance_score) * feedback_credibility * 0.4
                self._envy_level = min(1.0, self._envy_level + envy_boost)
                # Envy reduces pride
                pride_reduction = envy_boost * 0.3
                self._pride_level = max(0.0, self._pride_level - pride_reduction)

        except Exception as e:
            self.get_logger().warn(f"Failed to process performance feedback: {e}")

    def _on_social_feedback(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Direct social feedback affects authenticity and conformity pressure
            feedback_valence = data.get("valence", 0.5)     # 0=negative  1=positive
            feedback_authenticity = data.get("authenticity", 0.5) # How genuine the feedback is
            feedback_conformity = data.get("conformity", 0.5) # Pressure to conform
            feedback_source = data.get("source", "peer")    # Source of feedback

            # Authentic feedback increases authenticity
            authenticity_boost = feedback_authenticity * 0.2
            self._authenticity = min(1.0, self._authenticity + authenticity_boost)

            # Conformity feedback increases conformity pressure
            conformity_boost = feedback_conformity * 0.3
            self._conformity_pressure = min(1.0, self._conformity_pressure + conformity_boost)

            # Positive feedback increases social ranking
            ranking_boost = (feedback_valence - 0.5) * 0.4
            self._social_ranking = max(0.0, min(1.0, self._social_ranking + ranking_boost))

            # Negative feedback from credible sources increases envy
            if feedback_valence < 0.4 and feedback_authenticity > 0.6:
                envy_boost = (0.4 - feedback_valence) * feedback_authenticity * 0.3
                self._envy_level = min(1.0, self._envy_level + envy_boost)

        except Exception as e:
            self.get_logger().warn(f"Failed to process social feedback: {e}")

    def _on_others_achievements(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Others' achievements trigger social comparisons
            achievement_value = data.get("value", 0.5)      # 0=minor  1=major achievement
            achievement_relevance = data.get("relevance", 0.5) # Relevance to self
            achievement_effort = data.get("effort", 0.5)    # Perceived effort by others
            achievement_deserved = data.get("deserved", 0.5) # Whether achievement was seen as deserved

            # Others' achievements affect comparison direction
            # Better achievements by others -> negative comparison direction
            achievement_impact = achievement_value * achievement_relevance
            self._comparison_direction = -achievement_impact  # Negative because others doing better
            self._comparison_direction = max(-1.0, min(1.0, self._comparison_direction))

            # Undeserved achievements by others increase schadenfreude potential
            if achievement_deserved < 0.4 and achievement_value > 0.6:
                schadenfreude_boost = (achievement_value - 0.4) * (1.0 - achievement_deserved) * 0.3
                self._schadenfreude = min(1.0, self._schadenfreude + schadenfreude_boost)

            # High effort achievements by others increase envy
            if achievement_effort > 0.6 and achievement_value > 0.5:
                envy_boost = achievement_effort * achievement_value * 0.2
                self._envy_level = min(1.0, self._envy_level + envy_boost)

            # Relevant achievements increase comparison importance
            importance_boost = achievement_relevance * 0.2
            self._comparison_importance = min(1.0, self._comparison_importance + importance_boost)

        except Exception as e:
            self.get_logger().warn(f"Failed to process others' achievements: {e}")

    def _on_self_esteem_update(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Self-esteem affects how we process social comparisons
            self_esteem = data.get("esteem_level", 0.5)     # 0=low self-esteem  1=high self-esteem
            esteem_stability = data.get("stability", 0.5)   # How stable self-esteem is

            # High self-esteem reduces sensitivity to negative comparisons
            esteem_protection = (self_esteem - 0.5) * self._self_esteem_influence
            # Protects against negative comparison effects
            if self._comparison_direction < 0:  # Negative comparison (others better)
                protection_factor = 1.0 - esteem_protection
                self._comparison_direction *= protection_factor  # Reduce negative impact

            # Low self-esteem increases conformity pressure
            if self_esteem < 0.4:
                conformity_increase = (0.4 - self_esteem) * 0.3
                self._conformity_pressure = min(1.0, self._conformity_pressure + conformity_increase)

            # Stable self-esteem increases authenticity
            authenticity_boost = esteem_stability * 0.1
            self._authenticity = min(1.0, self._authenticity + authenticity_boost)

        except Exception as e:
            self.get_logger().warn(f"Failed to process self-esteem update: {e}")

    # ── Social Comparison Dynamics Update ────────────────────────────────────
    def _update_social_comparison(self):
        now = time.time()
        dt = now - self._last_update
        self._last_update = now

        # Natural decay of comparison effects over time
        decay = self._decay_rate * dt
        self._comparison_direction *= (1.0 - decay)
        self._comparison_importance = max(0.1, self._comparison_importance - decay * 0.5)
        self._social_ranking = 0.5 + (self._social_ranking - 0.5) * (1.0 - decay)
        self._envy_level = max(0.0, self._envy_level - decay)
        self._pride_level = max(0.0, self._pride_level - decay * 0.5)
        self._schadenfreude = max(0.0, self._schadenfreude - decay)
        self._competitiveness = max(0.0, self._competitiveness - decay * 0.3)
        self._conformity_pressure = max(0.0, self._conformity_pressure - decay * 0.4)
        self._authenticity = min(1.0, self._authenticity + decay * 0.05)  # Slow return to authentic

        # Empathy reduces negative social emotions
        empathy_reduction = self._empathy_factor * (self._envy_level + self._schadenfreude) * dt
        self._envy_level = max(0.0, self._envy_level - empathy_reduction)
        self._schadenfreude = max(0.0, self._schadenfreude - empathy_reduction)

        # High competitiveness increases comparison importance
        comp_influence = self._competitiveness * 0.1 * dt
        self._comparison_importance = min(1.0, self._comparison_importance + comp_influence)

        # High conformity pressure reduces authenticity
        conformity_effect = self._conformity_pressure * 0.05 * dt
        self._authenticity = max(0.0, self._authenticity - conformity_effect)

        # Authenticity reduces conformity pressure over time
        auth_effect = (1.0 - self._authenticity) * 0.02 * dt
        self._conformity_pressure = max(0.0, self._conformity_pressure - auth_effect)

        # Prepare outputs
        comparison_state = SocialComparisonState(
            timestamp=now,
            comparison_direction=self._comparison_direction,
            comparison_importance=self._comparison_importance,
            social_ranking=self._social_ranking,
            envy_level=self._envy_level,
            pride_level=self._pride_level,
            schadenfreude=self._schadenfreude,
            competitiveness=self._competitiveness,
            conformity_pressure=self._conformity_pressure,
            authenticity=self._authenticity
        )
        out = String()
        out.data = to_json(comparison_state)
        self._pub.publish(out)

        # Log significant social comparison dynamics
        if int(now) % 20 == 0:  # Every 20 seconds
            self.get_logger().info(
                f"Social Comparison - Dir:{self._comparison_direction:.2f} "
                f"Import:{self._comparison_importance:.2f} "
                f"Rank:{self._social_ranking:.2f} "
                f"Envy:{self._envy_level:.2f} "
                f"Pride:{self._pride_level:.2f}"
            )

def main(args=None):
    rclpy.init(args=args)
    node = SocialComparisonNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()