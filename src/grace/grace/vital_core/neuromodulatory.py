"""
grace_agi/vital_core/neuromodulatory.py
Vital Core — Neuromodulatory State
Models key neuromodulators: Dopamine, Cortisol, Oxytocin, Serotonin, Norepinephrine, Acetylcholine
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.grace.utils.schemas import NeuromodulatoryState, to_json


class NeuromodulatoryNode(Node):
    def __init__(self):
        super().__init__("grace_neuromodulatory")

        # ── Parameters ────────────────────────────────────────────────────────
        self.declare_parameter("update_hz", 0.05)  # Very slow biological timescale
        self.update_hz = self.get_parameter("update_hz").value

        # ── Internal State (Neuromodulator Levels) ───────────────────────────
        # All normalized 0-1 ranges representing typical physiological ranges
        self._dopamine = 0.5      # Reward, motivation, prediction error
        self._cortisol = 0.3      # Stress, arousal, alertness
        self._oxytocin = 0.4      # Social bonding, trust, affiliation
        self._serotonin = 0.6     # Mood regulation, impulse control
        self._norepinephrine = 0.4 # Attention, vigilance, arousal
        self._acetylcholine = 0.5 # Learning, memory, attention
        self._last_update = time.time()

        # ── Baseline Levels (Homeostatic Set Points) ────────────────────────
        self._baselines = {
            'dopamine': 0.5,
            'cortisol': 0.3,
            'oxytocin': 0.4,
            'serotonin': 0.6,
            'norepinephrine': 0.4,
            'acetylcholine': 0.5
        }

        # ── Subscribers (Inputs from other systems) ─────────────────────────
        # Drive inputs
        self.create_subscription(String, "/grace/vital/drive_state",
                                 self._on_drive_state, 10)
        # Stress/pain inputs
        self.create_subscription(String, "/grace/vital/pain_signal",
                                 self._on_pain, 10)
        # Social bonding inputs
        self.create_subscription(String, "/grace/subconscious/social_model",
                                 self._on_social_bonding, 10)
        # Reward inputs
        self.create_subscription(String, "/grace/unconscious/reward_signal",
                                 self._on_reward, 10)

        # ── Publishers (Outputs to other systems) ───────────────────────────
        self._pub = self.create_publisher(String, "/grace/vital/neuromodulatory_state", 10)
        self.create_timer(1.0 / self.update_hz, self._update_neuromodulators)
        self.get_logger().info("Neuromodulatory State ready.")

    # ── Input Processing ─────────────────────────────────────────────────────
    def _on_drive_state(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Energy levels affect dopamine (motivation)
            energy = data.get("energy_level", 0.5)
            curiosity = data.get("curiosity_level", 0.5)
            patience = data.get("patience_level", 0.5)

            # Low energy reduces dopamine (less motivation)
            # High curiosity increases dopamine (exploration drive)
            self._dopamine = 0.3 + 0.4 * energy + 0.3 * curiosity
            self._dopamine = max(0.0, min(1.0, self._dopamine))

            # Low patience increases norepinephrine (frustration/arousal)
            self._norepinephrine = 0.3 + 0.4 * (1.0 - patience)
            self._norepinephrine = max(0.0, min(1.0, self._norepinephrine))
        except Exception as e:
            self.get_logger().warn(f"Failed to process drive state: {e}")

    def _on_pain(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Pain increases cortisol (stress response)
            pain_level = data.get("pain_intensity", 0.0)
            self._cortisol = min(0.9, self._cortisol + pain_level * 0.5)
            # Chronic pain reduces serotonin (mood impact)
            self._serotonin = max(0.2, self._serotonin - pain_level * 0.01)
        except Exception as e:
            self.get_logger().warn(f"Failed to process pain signal: {e}")

    def _on_social_bonding(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Positive social interactions increase oxytocin
            social_positivity = data.get("bonding_quality", 0.0)
            self._oxytocin = min(0.9, self._oxytocin + social_positivity * 0.3)
            # Social bonding also increases serotonin (mood boost)
            self._serotonin = min(0.9, self._serotonin + social_positivity * 0.2)
        except Exception as e:
            self.get_logger().warn(f"Failed to process social bonding: {e}")

    def _on_reward(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Reward increases dopamine (reinforcement learning)
            reward_value = data.get("value", 0.0)  # -1 to +1
            if reward_value > 0:
                self._dopamine = min(0.9, self._dopamine + reward_value * 0.4)
            # Reward also affects serotonin (mood)
            self._serotonin = min(0.9, self._serotonin + abs(reward_value) * 0.2)
        except Exception as e:
            self.get_logger().warn(f"Failed to process reward: {e}")

    # ── Neuromodulator Dynamics ──────────────────────────────────────────────
    def _update_neuromodulators(self):
        now = time.time()
        dt = now - self._last_update
        self._last_update = now

        # Slow drift toward baselines (homeostatic regulation)
        time_constant = 10.0  # seconds to reach ~63% of baseline
        decay_factor = dt / time_constant

        neuromodulators = ['dopamine', 'cortisol', 'oxytocin', 'serotonin',
                          'norepinephrine', 'acetylcholine']

        for nm in neuromodulators:
            current = getattr(self, f'_{nm}')
            baseline = self._baselines[nm]
            # Exponential decay toward baseline
            new_value = current + (baseline - current) * decay_factor
            setattr(self, f'_{nm}', max(0.0, min(1.0, new_value)))

        # Publish neuromodulatory state
        nm_state = NeuromodulatoryState(
            timestamp=now,
            dopamine=self._dopamine,
            cortisol=self._cortisol,
            oxytocin=self._oxytocin,
            serotonin=self._serotonin,
            norepinephrine=self._norepinephrine,
            acetylcholine=self._acetylcholine
        )
        out = String()
        out.data = to_json(nm_state)
        self._pub.publish(out)

        # Log occasionally for monitoring
        if int(now) % 60 == 0:  # Every minute
            self.get_logger().info(
                f"NeuroMod - DA:{self._dopamine:.2f} "
                f"CORT:{self._cortisol:.2f} "
                f"OXY:{self._oxytocin:.2f} "
                f"5HT:{self._serotonin:.2f} "
                f"NE:{self._norepinephrine:.2f} "
                f"ACh:{self._acetylcholine:.2f}"
            )


def main(args=None):
    rclpy.init(args=args)
    node = NeuromodulatoryNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()