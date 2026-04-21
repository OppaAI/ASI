"""
grace_agi/subconscious/counterfactual_emotion.py
Subconscious Layer — Counterfactual Emotion Engine
Regret · Relief · Envy · Gratitude
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.grace.utils.schemas import CounterfactualEmotionState, to_json


class CounterfactualEmotionNode(Node):
    def __init__(self):
        super().__init__("grace_counterfactual_emotion")

        # ── Parameters ────────────────────────────────────────────────────────
        self.declare_parameter("update_hz", 0.1)  # Updates every 10 seconds
        self.update_hz = self.get_parameter("update_hz").value

        # ── Internal State ───────────────────────────────────────────────────
        self._regret = 0.2        # Emotion for bad outcomes from our actions
        self._relief = 0.3        # Emotion for bad outcomes avoided by inaction
        self._envy = 0.1          # Pain from others' good fortune
        self._gratitude = 0.4     # Thankfulness for benefits received
        self._last_update = time.time()

        # ── Emotion Dynamics Parameters ─────────────────────────────────────
        self._decay_rate = 0.01       # Natural decay of counterfactual emotions
        self._outcome_sensitivity = 0.4 # Sensitivity to actual vs expected outcomes
        self._social_comparison_weight = 0.3 # Weight of social comparisons in envy/gratitude
        self._learning_rate = 0.02    # How much we update expectations from outcomes

        # ── Subscribers (Inputs from other systems) ─────────────────────────
        # Action outcomes vs expectations
        self.create_subscription(String, "/grace/conscious/action_outcome",
                                 self._on_action_outcome, 10)
        # Inaction outcomes vs expectations
        self.create_subscription(String, "/grace/conscious/inaction_outcome",
                                 self._on_inaction_outcome, 10)
        # Social comparison information
        self.create_subscription(String, "/grace/unconscious/social_comparison",
                                 self._on_social_comparison, 10)
        # Received benefits and harms
        self.create_subscription(String, "/grace/social/benefits_received",
                                 self._on_benefits_received, 10)
        # Experienced harms and losses
        self.create_subscription(String, "/grace/social/harms_experienced",
                                 self._on_harms_experienced, 10)

        # ── Publishers (Outputs to other systems) ───────────────────────────
        self._pub = self.create_publisher(String, "/grace/subconscious/counterfactual_emotion_state", 10)
        self.create_timer(1.0 / self.update_hz, self._update_emotions)
        self.get_logger().info("Counterfactual Emotion Engine ready.")

    # ── Input Processing ─────────────────────────────────────────────────────
    def _on_action_outcome(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Regret: when we took action and got worse than expected outcome
            expected_value = data.get("expected_value", 0.5)  # What we predicted
            actual_value = data.get("actual_value", 0.5)     # What actually happened
            action_taken = data.get("action_taken", False)   # Did we act?

            if action_taken and actual_value < expected_value:
                # We acted and got worse than expected -> regret
                regret_magnitude = (expected_value - actual_value) * self._outcome_sensitivity
                self._regret = min(0.9, self._regret + regret_magnitude)
                # Regret reduces gratitude (conflicting emotions)
                self._gratitude = max(0.1, self._gratitude - regret_magnitude * 0.3)
            elif action_taken and actual_value > expected_value:
                # We acted and got better than expected -> happy surprise (not counterfactual)
                pass
        except Exception as e:
            self.get_logger().warn(f"Failed to process action outcome: {e}")

    def _on_inaction_outcome(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Relief: when we did NOT act and avoided a bad outcome
            expected_value = data.get("expected_value", 0.5)  # What we predicted would happen if we acted
            actual_value = data.get("actual_value", 0.5)     # What actually happened (we didn't act)
            action_available = data.get("action_available", True)  # Was action possible?

            if action_available and actual_value > expected_value:
                # We didn't act and avoided a bad outcome -> relief
                relief_magnitude = (actual_value - expected_value) * self._outcome_sensitivity
                self._relief = min(0.9, self._relief + relief_magnitude)
                # Relief can reduce regret (alternative emotional path)
                self._regret = max(0.1, self._regret - relief_magnitude * 0.2)
            elif action_available and actual_value < expected_value:
                # We didn't act and missed a good opportunity -> regret of inaction
                missed_opportunity = (expected_value - actual_value) * self._outcome_sensitivity
                self._regret = min(0.9, self._regret + missed_opportunity * 0.5)
        except Exception as e:
            self.get_logger().warn(f"Failed to process inaction outcome: {e}")

    def _on_social_comparison(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Envy: pain from others' good fortune (upward comparison)
            # Gratitude: thankfulness for benefits received (downward comparison or direct benefit)
            comparison_direction = data.get("direction", 0.0)  # -1=worse  0=same  1=better
            comparison_importance = data.get("importance", 0.5)
            comparison_domain = data.get("domain", "general")
            is_advantageous = data.get("is_advantageous", False)  # Did we benefit?

            if comparison_direction > 0.3 and comparison_importance > 0.4:
                # Others better than us -> envy
                envy_magnitude = (comparison_direction - 0.3) * comparison_importance * self._social_comparison_weight
                self._envy = min(0.8, self._envy + envy_magnitude)
                # Envy reduces gratitude (competing emotions)
                self._gratitude = max(0.1, self._gratitude - envy_magnitude * 0.2)
            elif comparison_direction < -0.3 and comparison_importance > 0.4:
                # Others worse than us -> potential for gratitude (if we see it as benefit)
                # Or satisfaction if we caused it
                if is_advantageous:
                    gratitude_magnitude = abs(comparison_direction + 0.3) * comparison_importance * 0.3
                    self._gratitude = min(0.9, self._gratitude + gratitude_magnitude)
        except Exception as e:
            self.get_logger().warn(f"Failed to process social comparison: {e}")

    def _on_benefits_received(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Direct benefits received increase gratitude
            benefit_value = data.get("value", 0.0)  # 0-1
            benefit_importance = data.get("importance", 0.5)
            source_intentionality = data.get("source_intentionality", 0.5)  # Was it intended to help us?

            gratitude_boost = benefit_value * benefit_importance * source_intentionality * 0.3
            self._gratitude = min(0.9, self._gratitude + gratitude_boost)
            # Gratitude reduces envy (competing positive emotion)
            self._envy = max(0.0, self._envy - gratitude_boost * 0.3)
        except Exception as e:
            self.get_logger().warn(f"Failed to process benefits received: {e}")

    def _on_harms_experienced(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Direct harms experienced can increase regret (if preventable) or reduce envy
            harm_value = data.get("value", 0.0)  # 0-1
            harm_preventable = data.get("harm_preventable", 0.5)  # Could we have avoided it?
            harm_importance = data.get("importance", 0.5)

            if harm_preventable > 0.5:
                # Harm we could have prevented -> regret
                regret_boost = harm_value * harm_preventable * harm_importance * 0.4
                self._regret = min(0.9, self._regret + regret_boost)
            # Experienced harms can reduce envy (others' good fortune less salient when we suffer)
            envy_reduction = harm_value * harm_importance * 0.2
            self._envy = max(0.0, self._envy - envy_reduction)
        except Exception as e:
            self.get_logger().warn(f"Failed to process harms experienced: {e}")

    # ── Emotion Dynamics Update ─────────────────────────────────────────────
    def _update_emotions(self):
        now = time.time()
        dt = now - self._last_update
        self._last_update = now

        # Natural decay of all counterfactual emotions
        decay = self._decay_rate * dt
        self._regret = max(0.0, self._regret - decay)
        self._relief = max(0.0, self._relief - decay)
        self._envy = max(0.0, self._envy - decay)
        self._gratitude = max(0.0, self._gratitude - decay)

        # Prepare outputs
        cf_emotion_state = CounterfactualEmotionState(
            timestamp=now,
            regret=self._regret,
            relief=self._relief,
            envy=self._envy,
            gratitude=self._gratitude,
            emotional_valence=self._calculate_net_valence(),
            complexity_score=self._calculate_complexity()
        )
        out = String()
        out.data = to_json(cf_emotion_state)
        self._pub.publish(out)

        # Log significant counterfactual emotions
        if int(now) % 15 == 0:  # Every 15 seconds
            self.get_logger().info(
                f"Counterfactual Emotion - Reg:{self._regret:.2f} "
                f"Rel:{self._relief:.2f} "
                f"Env:{self._envy:.2f} "
                f"Grat:{self._gratitude:.2f} "
                f"NetVal:{self._calculate_net_valence():.2f}"
            )

    def _calculate_net_valence(self) -> float:
        """Calculate net emotional valence of counterfactual emotions"""
        # Regret and envy are negative, relief and gratitude are positive
        negative_affect = self._regret + self._envy
        positive_affect = self._relief + self._gratitude
        return positive_affect - negative_affect

    def _calculate_complexity(self) -> float:
        """Calculate emotional complexity (entropy-like measure)"""
        emotions = [self._regret, self._relief, self._envy, self._gratitude]
        total = sum(emotions)
        if total == 0:
            return 0.0
        # Normalize to probabilities
        probs = [e/total for e in emotions]
        # Shannon entropy (higher = more complex/mixed emotional state)
        import math
        entropy = -sum(p * math.log(p) for p in probs if p > 0)
        return min(entropy, 2.0)  # Cap at reasonable maximum


def main(args=None):
    rclpy.init(args=args)
    node = CounterfactualEmotionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()