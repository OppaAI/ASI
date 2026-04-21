"""
grace_agi/subconscious/social_mirror.py
Subconscious Layer — Social Mirror & Identity Update
Looking-Glass Self · Sociometer
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.grace.utils.schemas import SocialMirrorState, to_json


class SocialMirrorNode(Node):
    def __init__(self):
        super().__init__("grace_social_mirror")

        # ── Parameters ────────────────────────────────────────────────────────
        self.declare_parameter("update_hz", 0.5)  # Updates twice per second
        self.update_hz = self.get_parameter("update_hz").value

        # ── Internal State ───────────────────────────────────────────────────
        self._looking_glass_self = 0.5     # How we believe others see us (0-1)
        self._actual_social_feedback = 0.5 # What actual social feedback indicates (0-1)
        self._self_esteem = 0.5            # Our overall self-esteem (0-1)
        self._sociometer_reading = 0.5     # Social inclusion/exclusion gauge (0-1)
        self._identity_coherence = 0.7     # How coherent our identity feels (0-1)
        self._last_update = time.time()

        # ── Social Mirror Parameters ─────────────────────────────────────────
        self._feedback_sensitivity = 0.4   # How much we update based on feedback
        self._identity_inertia = 0.7       # Resistance to identity change
        self._social_learning_rate = 0.2   # How fast we learn from social interactions
        self._self_verification_motive = 0.6 # Drive to confirm our self-views

        # ── Subscribers (Inputs from other systems) ─────────────────────────
        # Actual social feedback from interactions
        self.create_subscription(String, "/grace/subconscious/social_feedback",
                                 self._on_social_feedback, 10)
        # Our self-presentation attempts
        self.create_subscription(String, "/grace/conscious/action_execution",
                                 self._on_self_presentation, 10)
        # Social comparison information
        self.create_subscription(String, "/grace/unconscious/social_comparison",
                                 self._on_social_comparison, 10)
        # Identity challenges or confirmations
        self.create_subscription(String, "/grace/hidden/identity_challenge",
                                 self._on_identity_challenge, 10)
        # Autobiographical memory updates
        self.create_subscription(String, "/grace/subconscious/autobiographical_memory",
                                 self._on_autobiographical_memory, 10)

        # ── Publishers (Outputs to other systems) ───────────────────────────
        self._pub = self.create_publisher(String, "/grace/subconscious/social_mirror_state", 10)
        self.create_timer(1.0 / self.update_hz, self._update_social_mirror)
        self.get_logger().info("Social Mirror & Identity Update ready.")

    # ── Input Processing ─────────────────────────────────────────────────────
    def _on_social_feedback(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Actual feedback from social interactions
            feedback_valence = data.get("valence", 0.5)  # 0=negative  1=positive
            feedback_importance = data.get("importance", 0.5)  # How meaningful
            feedback_source_credibility = data.get("source_credibility", 0.5)  # Trustworthiness

            # Weight feedback by importance and credibility
            weighted_feedback = feedback_valence * feedback_importance * feedback_source_credibility
            self._actual_social_feedback = weighted_feedback
        except Exception as e:
            self.get_logger().warn(f"Failed to process social feedback: {e}")

    def _on_self_presentation(self, msg: String):
        try:
            data = json.loads(msg.data)
            # How we present ourselves influences looking-glass self through feedback loops
            presentation_confidence = data.get("confidence", 0.5)  # 0-1
            presentation_authenticity = data.get("authenticity", 0.5)  # 0-1
            social_context = data.get("context", "neutral")

            # Our presentation efforts shape what we think others see
            presentation_effect = (presentation_confidence + presentation_authenticity) / 2.0
            self._looking_glass_self = self._looking_glass_self * 0.9 + presentation_effect * 0.1
            self._looking_glass_self = max(0.0, min(1.0, self._looking_glass_self))
        except Exception as e:
            self.get_logger().warn(f"Failed to process self-presentation: {e}")

    def _on_social_comparison(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Social comparisons influence both looking-glass self and sociometer
            comparison_direction = data.get("direction", 0.0)  # -1=worse  0=same  1=better
            comparison_importance = data.get("importance", 0.5)
            comparison_domain = data.get("domain", "general")  # e.g., "competence", "morality", "appearance"

            # Upward comparisons (seeing others as better) can lower self-view
            # Downward comparisons (seeing others as worse) can raise self-view
            comparison_effect = comparison_direction * comparison_importance * 0.3
            self._looking_glass_self = max(0.0, min(1.0, self._looking_glass_self + comparison_effect))

            # Social comparisons also affect sociometer (sense of belonging)
            belonging_effect = -abs(comparison_direction) * comparison_importance * 0.2  # Any comparison reduces belonging slightly
            self._sociometer_reading = max(0.0, min(1.0, self._sociometer_reading + belonging_effect))
        except Exception as e:
            self.get_logger().warn(f"Failed to process social comparison: {e}")

    def _on_identity_challenge(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Direct challenges to our identity
            challenge_strength = data.get("strength", 0.0)  # 0-1
            challenge_domain = data.get("domain", "general")  # e.g., "competence", "morality", "beliefs"
            challenge_source = data.get("source", "unknown")  # Who/what is challenging

            # Identity challenges create dissonance that motivates change or defense
            challenge_impact = challenge_strength * 0.4
            # Temporarily reduce identity coherence when challenged
            self._identity_coherence = max(0.3, self._identity_coherence - challenge_impact)
            # May motivate identity update through looking-glass processes
        except Exception as e:
            self.get_logger().warn(f"Failed to process identity challenge: {e}")

    def _on_autobiographical_memory(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Autobiographical memory provides evidence for identity
            memory_content = data.get("content", "")
            memory_importance = data.get("importance", 0.5)
            memory_valence = data.get("emotional_tag", 0.0)  # -1 to 1
            memory_confidence = data.get("confidence", 0.5)

            # Positive, important, confident memories support identity coherence
            if memory_importance > 0.4 and memory_confidence > 0.5:
                identity_support = memory_valence * memory_importance * memory_confidence * 0.2
                self._identity_coherence = min(1.0, self._identity_coherence + identity_support)
                # Positive memories also boost self-esteem
                if memory_valence > 0:
                    self._self_esteem = min(1.0, self._self_esteem + memory_valence * 0.1)
        except Exception as e:
            self.get_logger().warn(f"Failed to process autobiographical memory: {e}")

    # ── Social Mirror Dynamics Update ───────────────────────────────────────
    def _update_social_mirror(self):
        now = time.time()
        dt = now - self._last_update
        self._last_update = now

        # Looking-glass self updates based on actual social feedback
        # But with inertia - we don't instantly change our self-view
        feedback_influence = (self._actual_social_feedback - self._looking_glass_self) * \
                           self._feedback_sensitivity * self._social_learning_rate * dt
        self._looking_glass_self += feedback_influence
        self._looking_glass_self = max(0.0, min(1.0, self._looking_glass_self))

        # Self-esteem updates based on looking-glass self and sociometer
        # We feel better when we think others see us positively and we feel included
        social_approval = (self._looking_glass_self + self._sociometer_reading) / 2.0
        self_esteem_target = 0.3 + social_approval * 0.4  # Baseline 0.3, up to 0.7 from social factors
        self_esteem_influence = (self_esteem_target - self._self_esteem) * \
                               self._social_learning_rate * dt
        self._self_esteem += self_esteem_influence
        self._self_esteem = max(0.0, min(1.0, self._self_esteem))

        # Sociometer updates based on actual inclusion signals
        # (In a full implementation, this would come from direct social inclusion/exclusion metrics)
        # For now, we'll simulate based on social feedback and comparison
        inclusion_signal = (self._actual_social_feedback * 0.6) + \
                          ((1.0 - abs(self._looking_glass_self - 0.5) * 2.0) * 0.4)  # Balance and feedback
        self_sociometer_target = inclusion_signal
        sociometer_influence = (self_sociometer_target - self._sociometer_reading) * \
                              self._social_learning_rate * dt
        self._sociometer_reading += sociometer_influence
        self._sociometer_reading = max(0.0, min(1.0, self._sociometer_reading))

        # Identity coherence increases when looking-glass self matches actual feedback
        # And when we have consistent self-esteem over time
        congruence = 1.0 - abs(self._looking_glass_self - self._actual_social_feedback)
        identity_coherence_target = 0.5 + congruence * 0.4  # Ranges from 0.5 to 0.9
        # Identity coherence also supported by stable self-esteem
        esteem_stability = 1.0 - abs(self._self_esteem - 0.5) * 0.4  # Penalty for extreme self-esteem
        identity_coherence_target = identity_coherence_target * (0.5 + esteem_stability * 0.5)

        coherence_influence = (identity_coherence_target - self._identity_coherence) * \
                             self._identity_inertia * dt
        self._identity_coherence += coherence_influence
        self._identity_coherence = max(0.0, min(1.0, self._identity_coherence))

        # Self-verification motive: we seek to confirm our existing self-views
        # Stronger when identity coherence is low
        verification_motive_base = 0.3
        verification_motive_boost = (1.0 - self._identity_coherence) * 0.4
        self._self_verification_motive = min(0.9, verification_motive_base + verification_motive_boost)

        # Prepare outputs
        social_mirror_state = SocialMirrorState(
            timestamp=now,
            looking_glass_self=self._looking_glass_self,
            actual_social_feedback=self._actual_social_feedback,
            self_esteem=self._self_esteem,
            sociometer_reading=self._sociometer_reading,
            identity_coherence=self._identity_coherence,
            self_verification_motive=self._self_verification_motive,
            congruence=congruence
        )
        out = String()
        out.data = to_json(social_mirror_state)
        self._pub.publish(out)

        # Log significant identity dynamics
        if int(now) % 20 == 0:  # Every 20 seconds
            self.get_logger().info(
                f"Social Mirror - LGS:{self._looking_glass_self:.2f} "
                f"ASF:{self._actual_social_feedback:.2f} "
                f"SE:{self._self_esteem:.2f} "
                f"SocM:{self._sociometer_reading:.2f} "
                f"IDC:{self._identity_coherence:.2f}"
            )


def main(args=None):
    rclpy.init(args=args)
    node = SocialMirrorNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()