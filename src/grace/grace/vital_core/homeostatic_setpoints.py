"""
grace_agi/vital_core/homeostatic_setpoints.py
Vital Core — Homeostatic Set Points
Optimal Arousal · Comfort Zones · Baseline Mood
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.grace.utils.schemas import HomeostaticSetPoints, to_json


class HomeostaticSetPointsNode(Node):
    def __init__(self):
        super().__init__("grace_homeostatic_setpoints")

        # ── Parameters ────────────────────────────────────────────────────────
        self.declare_parameter("update_hz", 0.001)  # Very slow - these are traits
        self.update_hz = self.get_parameter("update_hz").value

        # ── Internal State (Relatively Stable Traits) ─────────────────────────
        # These represent individual differences that change slowly over time
        self._optimal_arousal = 0.5      # 0=low arousal preferred  1=high arousal preferred
        self._comfort_zone_width = 0.6   # 0=narrow comfort zone  1=wide tolerance
        self._baseline_mood = 0.5        # 0=negative  1=positive (affective baseline)
        self._stress_tolerance = 0.5     # 0=low tolerance  1=high tolerance
        self._reward_sensitivity = 0.5   # 0=insensitive  1=highly sensitive
        self._last_update = time.time()

        # ── Plasticity Parameters (How set points can change) ─────────────────
        self._arousal_plasticity = 0.0001    # Very slow change
        self._comfort_plasticity = 0.00005   # Even slower
        self._mood_plasticity = 0.0002       # Moderately slow (can shift with therapy)
        self._stress_plasticity = 0.0001
        self._reward_plasticity = 0.00015

        # ── Subscribers (Inputs for long-term plasticity) ───────────────────
        # Chronic stress exposure shapes stress tolerance
        self.create_subscription(String, "/grace/vital/allostatic_load",
                                 self._on_chronic_load, 10)
        # Positive experiences shape reward sensitivity and mood
        self.create_subscription(String, "/grace/reward/positive_experience",
                                 self._on_positive_experience, 10)
        # Social acceptance shapes comfort zone and baseline mood
        self.create_subscription(String, "/grace/social/acceptance_signals",
                                 self._on_social_acceptance, 10)
        # Learning and mastery experiences shape optimal arousal
        self.create_subscription(String, "/grace/learning/mastery_experience",
                                 self._on_mastery_experience, 10)

        # ── Publishers (Outputs to other systems) ───────────────────────────
        self._pub = self.create_publisher(String, "/grace/vital/homeostatic_setpoints", 10)
        self.create_timer(1.0 / self.update_hz, self._update_setpoints)
        self.get_logger().info("Homeostatic Set Points ready.")

    # ── Input Processing for Long-term Plasticity ───────────────────────────
    def _on_chronic_load(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Chronic high allostatic load decreases stress tolerance
            load_level = data.get("allostatic_load", 0.0)
            if load_level > 1.0:  # Chronically high load
                # Decrease stress tolerance (become more sensitive)
                change = -self._stress_plasticity * (load_level - 1.0) * 0.1
                self._stress_tolerance = max(0.1, self._stress_tolerance + change)
                # Increase baseline anxiety component of mood
                self._baseline_mood = max(0.1, self._baseline_mood - change * 0.5)
        except Exception as e:
            self.get_logger().warn(f"Failed to process chronic load: {e}")

    def _on_positive_experience(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Positive experiences increase reward sensitivity and improve mood
            positivity = data.get("positivity", 0.0)  # 0-1
            significance = data.get("significance", 0.5)  # How meaningful

            # Increase reward sensitivity
            reward_change = self._reward_plasticity * positivity * significance * 0.5
            self._reward_sensitivity = min(0.9, self._reward_sensitivity + reward_change)

            # Improve baseline mood
            mood_change = self._mood_plasticity * positivity * significance * 0.3
            self._baseline_mood = min(0.9, self._baseline_mood + mood_change)

            # Slightly widen comfort zone with positive experiences
            comfort_change = self._comfort_plasticity * positivity * 0.2
            self._comfort_zone_width = min(0.9, self._comfort_zone_width + comfort_change)
        except Exception as e:
            self.get_logger().warn(f"Failed to process positive experience: {e}")

    def _on_social_acceptance(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Social acceptance increases comfort zone width and baseline mood
            acceptance = data.get("acceptance_level", 0.0)  # 0=rejected  1=accepted
            consistency = data.get("consistency", 0.5)    # How consistent over time

            # Widen comfort zone with social acceptance
            comfort_change = self._comfort_plasticity * acceptance * consistency * 0.3
            self._comfort_zone_width = min(0.9, self._comfort_zone_width + comfort_change)

            # Improve baseline mood through belonging
            mood_change = self._mood_plasticity * acceptance * consistency * 0.4
            self._baseline_mood = min(0.9, self._baseline_mood + mood_change)

            # Social acceptance can slightly reduce optimal arousal need (more secure)
            arousal_change = -self._arousal_plasticity * acceptance * 0.1
            self._optimal_arousal = max(0.1, min(0.9, self._optimal_arousal + arousal_change))
        except Exception as e:
            self.get_logger().warn(f"Failed to process social acceptance: {e}")

    def _on_mastery_experience(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Mastery experiences increase optimal arousal preference (seek challenges)
            mastery_level = data.get("mastery_level", 0.0)  # 0=novice  1=expert
            challenge_rating = data.get("challenge_rating", 0.5)  # How challenging

            # Successful mastery increases preference for optimal arousal
            mastery_change = self._arousal_plasticity * mastery_level * challenge_rating * 0.4
            self._optimal_arousal = min(0.9, self._optimal_arousal + mastery_change)

            # Also increases confidence component of mood
            mood_change = self._mood_plasticity * mastery_level * 0.2
            self._baseline_mood = min(0.9, self._baseline_mood + mood_change)
        except Exception as e:
            self.get_logger().warn(f"Failed to process mastery experience: {e}")

    # ── Set Points Dynamics (Very Slow Change) ──────────────────────────────
    def _update_setpoints(self):
        now = time.time()
        dt = now - self._last_update
        self._last_update = now

        # Very slow drift toward neutral set points (unless modified by experience)
        # This represents genetic/developmental tendencies pulling back toward mean

        # Optimal arousal drifts toward population mean (0.5)
        arousal_drift = (0.5 - self._optimal_arousal) * self._arousal_plasticity * 0.1
        self._optimal_arousal += arousal_drift
        self._optimal_arousal = max(0.1, min(0.9, self._optimal_arousal))

        # Comfort zone width drifts toward moderate (0.5)
        comfort_drift = (0.5 - self._comfort_zone_width) * self._comfort_plasticity * 0.1
        self._comfort_zone_width += comfort_drift
        self._comfort_zone_width = max(0.2, min(0.9, self._comfort_zone_width))

        # Baseline mood drifts toward slightly positive (0.6) - Pollyanna principle
        mood_drift = (0.6 - self._baseline_mood) * self._mood_plasticity * 0.1
        self._baseline_mood += mood_drift
        self._baseline_mood = max(0.1, min(0.9, self._baseline_mood))

        # Stress tolerance drifts toward moderate (0.5)
        stress_drift = (0.5 - self._stress_tolerance) * self._stress_plasticity * 0.1
        self._stress_tolerance += stress_drift
        self._stress_tolerance = max(0.1, min(0.9, self._stress_tolerance))

        # Reward sensitivity drifts toward moderate (0.5)
        reward_drift = (0.5 - self._reward_sensitivity) * self._reward_plasticity * 0.1
        self._reward_sensitivity += reward_drift
        self._reward_sensitivity = max(0.1, min(0.9, self._reward_sensitivity))

        # Publish set points
        setpoints = HomeostaticSetPoints(
            timestamp=now,
            optimal_arousal=self._optimal_arousal,
            comfort_zone_width=self._comfort_zone_width,
            baseline_mood=self._baseline_mood,
            stress_tolerance=self._stress_tolerance,
            reward_sensitivity=self._reward_sensitivity
        )
        out = String()
        out.data = to_json(setpoints)
        self._pub.publish(out)

        # Log significant changes occasionally (very rare)
        if int(now) % 86400 == 0:  # Once per day
            self.get_logger().info(
                f"Set Points - Arousal:{self._optimal_arousal:.2f} "
                f"Comfort:{self._comfort_zone_width:.2f} "
                f"Mood:{self._baseline_mood:.2f} "
                f"StressTol:{self._stress_tolerance:.2f} "
                f"RewardSens:{self._reward_sensitivity:.2f}"
            )


def main(args=None):
    rclpy.init(args=args)
    node = HomeostaticSetPointsNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()