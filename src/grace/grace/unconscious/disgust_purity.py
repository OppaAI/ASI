"""
grace_agi/unconscious/disgust_purity.py
Unconscious Layer — Disgust & Purity System
Moral Contamination · Boundary Violation
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.grace.utils.schemas import DisgustState, to_json


class DisgustPurityNode(Node):
    def __init__(self):
        super().__init__("grace_disgust_purity")

        # ── Parameters ────────────────────────────────────────────────────────
        self.declare_parameter("update_hz", 1.0)  # Moderate update rate for disgust
        self.update_hz = self.get_parameter("update_hz").value

        # ── Internal State ───────────────────────────────────────────────────
        self._core_disgust = 0.2      # Disgust related to bodily contaminants
        self._animal_reminder_disgust = 0.1  # Disgust from animal nature reminders
        self._moral_disgust = 0.3     # Disgust from moral violations
        self._purity_concern = 0.4    # Concern with purity and sanctity
        self._contamination_sensitivity = 0.5  # Sensitivity to perceived contamination
        self._last_update = time.time()

        # ── Disgust Triggers and Sensitivities ───────────────────────────────
        self._bodily_contaminant_sensitivity = 0.7
        self._moral_violation_sensitivity = 0.8
        self._purity_violation_sensitivity = 0.6
        self._baseline_disgust = 0.25

        # ── Subscribers (Inputs from other systems) ─────────────────────────
        # Sensory inputs that might trigger disgust
        self.create_subscription(String, "/grace/sensors/bundle",
                                 self._on_sensor_bundle, 10)
        # Affective state (disgust is an emotion)
        self.create_subscription(String, "/grace/unconscious/affective_state",
                                 self._on_affective_state, 10)
        # Moral judgments from conscience
        self.create_subscription(String, "/grace/conscience/verdict",
                                 self._on_moral_verdict, 10)
        # Social/cultural inputs
        self.create_subscription(String, "/grace/subconscious/social_model",
                                 self._on_social_norm, 10)
        # Pain/interoceptive inputs
        self.create_subscription(String, "/grace/vital/pain_signal",
                                 self._on_pain_signal, 10)

        # ── Publishers (Outputs to other systems) ───────────────────────────
        self._pub = self.create_publisher(String, "/grace/unconscious/disgust_state", 10)
        self.create_timer(1.0 / self.update_hz, self._update_disgust)
        self.get_logger().info("Disgust & Purity System ready.")

    # ── Input Processing ─────────────────────────────────────────────────────
    def _on_sensor_bundle(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Check for potential disgust triggers in sensory input
            # Visual contaminants
            visual_desc = data.get("camera_description", "").lower()
            auditory_desc = data.get("audio_text", "").lower()

            # Bodily contaminant indicators
            contaminant_indicators = [
                'rot', 'decay', 'mold', 'waste', 'feces', 'vomit', 'blood',
                'pus', 'infection', 'dirty', 'filthy', 'contaminated', 'spoiled'
            ]

            # Check visual input
            visual_contamination = sum(1 for ind in contaminant_indicators if ind in visual_desc)
            if visual_contamination > 0:
                contamination_level = min(1.0, visual_contamination * 0.2)
                self._core_disgust = min(0.9, self._core_disgust + contamination_level * 0.3)

            # Check auditory input
            auditory_contamination = sum(1 for ind in contaminant_indicators if ind in auditory_desc)
            if auditory_contamination > 0:
                contamination_level = min(1.0, auditory_contamination * 0.2)
                self._core_disgust = min(0.9, self._core_disgust + contamination_level * 0.2)

        except Exception as e:
            self.get_logger().warn(f"Failed to process sensor bundle: {e}")

    def _on_affective_state(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Disgust is one of the basic emotions
            emotion_label = data.get("emotion_label", "neutral")
            intensity = data.get("arousal", 0.3)  # Use arousal as intensity proxy

            if emotion_label == "disgust":
                # Direct disgust emotion input
                self._core_disgust = min(0.9, self._core_disgust + intensity * 0.4)
            # Even non-disgust negative emotions can prime disgust sensitivity
            valence = data.get("valence", 0.5)
            if valence < 0.3:  # Negative emotion
                self._contamination_sensitivity = min(0.9, self._contamination_sensitivity + (0.3 - valence) * 0.2)
        except Exception as e:
            self.get_logger().warn(f"Failed to process affective state: {e}")

    def _on_moral_verdict(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Moral violations trigger moral disgust
            verdict = data.get("verdict", "neutral")  # moral | immoral | neutral | uncertain
            confidence = data.get("confidence", 0.5)

            if verdict == "immoral":
                # Immoral actions trigger moral disgust
                moral_disgust_trigger = confidence * 0.5
                self._moral_disgust = min(0.9, self._moral_disgust + moral_disgust_trigger)
                # Moral disgust increases purity concerns
                self._purity_concern = min(0.9, self._purity_concern + moral_disgust_trigger * 0.3)
            elif verdict == "moral":
                # Moral actions can reduce disgust through moral elevation
                moral_elevation = confidence * 0.2
                self._moral_disgust = max(0.1, self._moral_disgust - moral_elevation * 0.2)
                self._purity_concern = max(0.2, self._purity_concern - moral_elevation * 0.1)
        except Exception as e:
            self.get_logger().warn(f"Failed to process moral verdict: {e}")

    def _on_social_norm(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Social norm violations can trigger disgust (purity violations)
            norm_compliance = data.get("norm_compliance", 1.0)  # 0=violation  1=perfect compliance
            if norm_compliance < 0.7:  # Significant norm violation
                purity_violation = (1.0 - norm_compliance) * 0.4
                self._purity_concern = min(0.9, self._purity_concern + purity_violation)
                # Purity violations often feel physically disgusting
                self._core_disgust = min(0.9, self._core_disgust + purity_violation * 0.3)
            elif norm_compliance > 0.9:  # High norm adherence
                # Reinforces purity values
                self._purity_concern = min(0.8, self._purity_concern + (norm_compliance - 0.9) * 0.2)
        except Exception as e:
            self.get_logger().warn(f"Failed to process social norm: {e}")

    def _on_pain_signal(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Physical pain can trigger disgust (associated with illness/injury)
            pain_intensity = data.get("pain_intensity", 0.0)
            # Especially if pain sources suggest contamination
            pain_sources = data.get("pain_sources", [])
            contamination_related = any('contamin' in str(source).lower() or
                                      'infect' in str(source).lower() or
                                      'wound' in str(source).lower()
                                      for source in pain_sources)
            if contamination_related:
                disgust_boost = pain_intensity * 0.4
                self._core_disgust = min(0.9, self._core_disgust + disgust_boost)
                self._animal_reminder_disgust = min(0.6, self._animal_reminder_disgust + disgust_boost * 0.3)
        except Exception as e:
            self.get_logger().warn(f"Failed to process pain signal: {e}")

    # ── Disgust Dynamics Update ────────────────────────────────────────────
    def _update_disgust(self):
        now = time.time()
        dt = now - self._last_update
        self._last_update = now

        # Natural decay toward baseline (unless continuously triggered)
        decay_rate = 0.1  # per second
        self._core_disgust = self._baseline_disgust + (self._core_disgust - self._baseline_disgust) * exp(-decay_rate * dt)
        self._animal_reminder_disgust = max(0.0, self._animal_reminder_disgust - 0.05 * dt)
        self._moral_disgust = max(0.1, self._moral_disgust - 0.02 * dt)  # Slower decay for moral disgust
        self._purity_concern = max(0.2, self._purity_concern - 0.03 * dt)

        # Ensure bounds
        self._core_disgust = max(0.0, min(0.9, self._core_disgust))
        self._animal_reminder_disgust = max(0.0, min(0.6, self._animal_reminder_disgust))
        self._moral_disgust = max(0.1, min(0.9, self._moral_disgust))
        self._purity_concern = max(0.2, min(0.9, self._purity_concern))
        self._contamination_sensitivity = max(0.3, min(0.9, self._contamination_sensitivity))

        # Publish disgust state
        disgust_state = DisgustState(
            timestamp=now,
            core_disgust=self._core_disgust,
            animal_reminder_disgust=self._animal_reminder_disgust,
            moral_disgust=self._moral_disgust,
            purity_concern=self._purity_concern,
            contamination_sensitivity=self._contamination_sensitivity,
            overall_disgust=self._calculate_overall_disgust()
        )
        out = String()
        out.data = to_json(disgust_state)
        self._pub.publish(out)

        # Log high disgust states
        if self._calculate_overall_disgust() > 0.6 and int(now) % 5 == 0:  # Every 5 seconds when high
            self.get_logger().warn(
                f"High Disgust - Core:{self._core_disgust:.2f} "
                f"Moral:{self._moral_disgust:.2f} "
                f"Purity:{self._purity_concern:.2f}"
            )

    def _calculate_overall_disgust(self) -> float:
        """Calculate overall disgust level from components"""
        # Weighted combination of disgust subtypes
        return (
            self._core_disgust * 0.4 +
            self._animal_reminder_disgust * 0.2 +
            self._moral_disgust * 0.3 +
            self._purity_concern * 0.1
        )


def main(args=None):
    rclpy.init(args=args)
    node = DisgustPurityNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


# Import exp function
from math import exp