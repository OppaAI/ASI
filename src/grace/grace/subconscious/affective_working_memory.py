"""
grace_agi/subconscious/affective_working_memory.py
Subconscious Layer — Affective Working Memory
Mood regulation · Emotional inertia · Affective capacity
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.grace.utils.schemas import AffectiveWorkingMemoryState, to_json


class AffectiveWorkingMemoryNode(Node):
    def __init__(self):
        super().__init__("grace_affective_working_memory")

        # ── Parameters ────────────────────────────────────────────────────────
        self.declare_parameter("update_hz", 0.5)  # Updates twice per second
        self.update_hz = self.get_parameter("update_hz").value

        # ── Internal State ───────────────────────────────────────────────────
        self._current_mood = 0.5               # -1=negative  0=neutral  1=positive
        self._mood_stability = 0.7             # 0=unstable  1=stable
        self._emotional_inertia = 0.3          # 0=fluid  1=rigid (resistance to change)
        self._mood_congruent_bias = 0.2        # Tendency to recall mood-congruent memories
        self._affective_capacity = 0.6         # Current affective processing load (0-1)
        self._dominant_emotion = "neutral"     # Currently dominant emotion label
        self._emotion_variability = 0.4        # 0=stable  1=highly variable
        self._stress_buffer = 0.5              # 0=no buffer  1=high buffering capacity
        self._last_update = time.time()

        # ── Affective Working Memory Parameters ───────────────────────────────
        self._mood_decay_rate = 0.01           # Natural return to neutral mood
        self._capacity_recovery_rate = 0.02    # Recovery of affective capacity
        self._buffer_recovery_rate = 0.015     # Recovery of stress buffer
        self._emotion_influence_weight = 0.4   # Weight of incoming emotional signals

        # ── Subscribers (Inputs from other systems) ─────────────────────────
        # Current affective state from unconscious layer
        self.create_subscription(String, "/grace/unconscious/affective_state",
                                 self._on_affective_state, 10)
        # Counterfactual emotions for mood influence
        self.create_subscription(String, "/grace/subconscious/counterfactual_emotion_state",
                                 self._on_counterfactual_emotion, 10)
        # Social feedback influencing mood
        self.create_subscription(String, "/grace/subconscious/social_mirror_state",
                                 self._on_social_mirror, 10)
        # Stress signals from vital systems
        self.create_subscription(String, "/grace/vital/allostatic_load",
                                 self._on_allostatic_load, 10)
        # Homeostatic drives affecting mood
        self.create_subscription(String, "/grace/vital/homeostatic_drive_state",
                                 self._on_homeostatic_drive, 10)

        # ── Publishers (Outputs to other systems) ───────────────────────────
        self._pub = self.create_publisher(String, "/grace/subconscious/affective_working_memory_state", 10)
        self.create_timer(1.0 / self.update_hz, self._update_affective_working_memory)
        self.get_logger().info("Affective Working Memory ready.")

    # ── Input Processing ─────────────────────────────────────────────────────
    def _on_affective_state(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Integrate current affective state into working memory
            valence = data.get("valence", 0.5)   # 0=negative  1=positive
            arousal = data.get("arousal", 0.3)   # 0=calm  1=excited
            dominance = data.get("dominance", 0.5)  # 0=submissive 1=dominant

            # Convert valence to -1 to 1 range for mood integration
            mood_signal = (valence - 0.5) * 2.0  # Convert 0-1 to -1-1
            dominance_signal = (dominance - 0.5) * 2.0  # Convert 0-1 to -1-1

            # Update mood with emotional inertia
            mood_change = mood_signal * self._emotion_influence_weight
            self._current_mood += mood_change * (1.0 - self._emotional_inertia)
            self._current_mood = max(-1.0, min(1.0, self._current_mood))

            # Update dominant emotion label based on valence and arousal
            self._update_dominant_emotion_label(valence, arousal, dominance)

        except Exception as e:
            self.get_logger().warn(f"Failed to process affective state: {e}")

    def _on_counterfactual_emotion(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Counterfactual emotions influence mood and affective capacity
            regret = data.get("regret", 0.2)
            relief = data.get("relief", 0.3)
            envy = data.get("envy", 0.1)
            gratitude = data.get("gratitude", 0.4)
            net_valence = data.get("emotional_valence", 0.0)

            # Net negative emotions increase load and decrease stability
            negative_load = (regret + envy) * 0.3
            positive_load = (relief + gratitude) * 0.2
            net_emotional_load = negative_load - positive_load

            # Update affective capacity based on load
            self._affective_capacity = min(1.0, max(0.0,
                self._affective_capacity + net_emotional_load * 0.1))

            # Mood shifts based on net valence
            mood_shift = net_valence * 0.2
            self._current_mood += mood_shift * (1.0 - self._emotional_inertia)
            self._current_mood = max(-1.0, min(1.0, self._current_mood))

        except Exception as e:
            self.get_logger().warn(f"Failed to process counterfactual emotion: {e}")

    def _on_social_mirror(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Social feedback influences mood and self-esteem components
            looking_glass_self = data.get("looking_glass_self", 0.5)
            actual_social_feedback = data.get("actual_social_feedback", 0.5)
            self_esteem = data.get("self_esteem", 0.5)
            sociometer_reading = data.get("sociometer_reading", 0.5)

            # Positive social feedback improves mood
            social_mood_signal = ((looking_glass_self + actual_social_feedback) / 2.0 - 0.5) * 2.0
            self._current_mood += social_mood_signal * 0.15

            # Social inclusion affects stress buffer
            inclusion_signal = (sociometer_reading - 0.5) * 2.0  # Convert to -1 to 1
            self._stress_buffer += inclusion_signal * 0.1
            self._stress_buffer = max(0.0, min(1.0, self._stress_buffer))

            # Update dominant emotion based on social context
            self._update_dominant_emotion_from_social(looking_glass_self, actual_social_feedback, self_esteem)

        except Exception as e:
            self.get_logger().warn(f"Failed to process social mirror: {e}")

    def _on_allostatic_load(self, msg: String):
        try:
            data = json.loads(msg.data)
            # High allostatic load reduces affective capacity and increases variability
            allostatic_load = data.get("allostatic_load", 0.0)  # 0=no load  2+=overwhelming
            cognitive_cost = data.get("cognitive_cost_today", 0.0)  # Daily cognitive expenditure
            instantaneous_load = data.get("instantaneous_load", 0.0)  # Recent stress accumulator

            # High load decreases mood stability and increases variability
            load_impact = min(1.0, allostatic_load / 2.0)  # Normalize 0-2 to 0-1
            self._mood_stability = max(0.1, self._mood_stability - load_impact * 0.2)
            self._emotion_variability = min(0.9, self._emotion_variability + load_impact * 0.3)

            # High load decreases affective capacity
            capacity_reduction = (cognitive_cost + instantaneous_load) * 0.1
            self._affective_capacity = max(0.1, self._affective_capacity - capacity_reduction)

        except Exception as e:
            self.get_logger().warn(f"Failed to process allostatic load: {e}")

    def _on_homeostatic_drive(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Homeostatic drives influence mood (e.g., hunger -> irritability)
            energy_level = data.get("energy_level", 1.0)      # 0=depleted  1=optimal
            curiosity_level = data.get("curiosity_level", 0.7) # 0=no interest  1=highly curious
            patience_level = data.get("patience_level", 0.8)   # 0=impulsive  1=patient

            # Low energy negatively affects mood
            energy_mood_effect = (energy_level - 0.5) * 0.3  # -0.15 to +0.15
            self._current_mood += energy_mood_effect * (1.0 - self._emotional_inertia)

            # Low patience increases emotional variability
            patience_variability_effect = (1.0 - patience_level) * 0.2
            self._emotion_variability = min(0.9, self._emotion_variability + patience_variability_effect)

            # High curiosity can increase mood variability but also capacity
            curiosity_effect = (curiosity_level - 0.5) * 0.1
            self._emotion_variability = min(0.9, self._emotion_variability + abs(curiosity_effect) * 0.1)
            self._affective_capacity = min(1.0, self._affective_capacity + curiosity_effect * 0.05)

        except Exception as e:
            self.get_logger().warn(f"Failed to process homeostatic drive: {e}")

    # ── Affective Working Memory Dynamics Update ──────────────────────────────
    def _update_affective_working_memory(self):
        now = time.time()
        dt = now - self._last_update
        self._last_update = now

        # Mood naturally decays toward neutral (0.0)
        mood_decay = self._mood_decay_rate * dt * (0.0 - self._current_mood)
        self._current_mood += mood_decay
        self._current_mood = max(-1.0, min(1.0, self._current_mood))

        # Mood stability recovers toward baseline when not perturbed
        stability_recovery = (0.7 - self._mood_stability) * self._capacity_recovery_rate * dt
        self._mood_stability += stability_recovery
        self._mood_stability = max(0.1, min(1.0, self._mood_stability))

        # Emotional inertia slowly adapts based on recent variability
        inertia_adjustment = (self._emotion_variability - 0.5) * 0.01 * dt
        self._emotional_inertia += inertia_adjustment
        self._emotional_inertia = max(0.1, min(0.9, self._emotional_inertia))

        # Affective capacity recovers when not overloaded
        capacity_recovery = (0.6 - self._affective_capacity) * self._capacity_recovery_rate * dt
        self._affective_capacity += capacity_recovery
        self._affective_capacity = max(0.1, min(1.0, self._affective_capacity))

        # Stress buffer recovers during low-stress periods
        buffer_recovery = (0.5 - self._stress_buffer) * self._buffer_recovery_rate * dt
        self._stress_buffer += buffer_recovery
        self._stress_buffer = max(0.0, min(1.0, self._stress_buffer))

        # Mood congruent bias increases with extreme moods
        mood_extremeness = abs(self._current_mood)
        self._mood_congruent_bias = 0.1 + mood_extremeness * 0.3  # 0.1 to 0.4

        # Prepare outputs
        affective_wm_state = AffectiveWorkingMemoryState(
            timestamp=now,
            current_mood=self._current_mood,
            mood_stability=self._mood_stability,
            emotional_inertia=self._emotional_inertia,
            mood_congruent_bias=self._mood_congruent_bias,
            affective_capacity=self._affective_capacity,
            dominant_emotion=self._dominant_emotion,
            emotion_variability=self._emotion_variability,
            stress_buffer=self._stress_buffer
        )
        out = String()
        out.data = to_json(affective_wm_state)
        self._pub.publish(out)

        # Log significant affective working memory dynamics
        if int(now) % 15 == 0:  # Every 15 seconds
            self.get_logger().info(
                f"Affective WM - Mood:{self._current_mood:.2f} "
                f"Stab:{self._mood_stability:.2f} "
                f"Inert:{self._emotional_inertia:.2f} "
                f"Cap:{self._affective_capacity:.2f} "
                f"DomEmo:{self._dominant_emotion}"
            )

    def _update_dominant_emotion_label(self, valence: float, arousal: float, dominance: float):
        """Update dominant emotion label based on valence, arousal, dominance"""
        # Simple emotion categorization based on valence-arousal space
        if valence >= 0.7 and arousal >= 0.6:
            self._dominant_emotion = "excited"
        elif valence >= 0.7 and arousal < 0.4:
            self._dominant_emotion = "content"
        elif valence <= 0.3 and arousal >= 0.6:
            self._dominant_emotion = "anxious"
        elif valence <= 0.3 and arousal < 0.4:
            self._dominant_emotion = "sad"
        elif arousal >= 0.7 and abs(valence - 0.5) < 0.2:
            self._dominant_emotion = "aroused"
        elif arousal < 0.3 and abs(valence - 0.5) < 0.2:
            self._dominant_emotion = "calm"
        elif dominance >= 0.7:
            self._dominant_emotion = "assertive"
        elif dominance <= 0.3:
            self._dominant_emotion = "submissive"
        else:
            self._dominant_emotion = "neutral"

    def _update_dominant_emotion_from_social(self, looking_glass_self: float, actual_social_feedback: float, self_esteem: float):
        """Update dominant emotion based on social context"""
        social_positivity = (looking_glass_self + actual_social_feedback) / 2.0
        if social_positivity >= 0.7 and self_esteem >= 0.6:
            self._dominant_emotion = "proud"
        elif social_positivity <= 0.3 and self_esteem <= 0.4:
            self._dominant_emotion = "ashamed"
        elif social_positivity >= 0.6 and self_esteem <= 0.4:
            self._dominant_emotion = "humble"
        elif social_positivity <= 0.4 and self_esteem >= 0.6:
            self._dominant_emotion = "confident"


def main(args=None):
    rclpy.init(args=args)
    node = AffectiveWorkingMemoryNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()