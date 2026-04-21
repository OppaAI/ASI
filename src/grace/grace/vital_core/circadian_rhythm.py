"""
grace_agi/vital_core/circadian_rhythm.py
Vital Core — Circadian & Ultradian Rhythm
Attention · Creativity · Energy Cycles
"""
import json, time, math, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.grace.utils.schemas import CircadianRhythm, to_json


class CircadianRhythmNode(Node):
    def __init__(self):
        super().__init__("grace_circadian_rhythm")

        # ── Parameters ────────────────────────────────────────────────────────
        self.declare_parameter("update_hz", 0.01)  # Update every 100 seconds for smooth cycles
        self.update_hz = self.get_parameter("update_hz").value

        # ── Internal State ───────────────────────────────────────────────────
        self._last_update = time.time()
        self._cycle_phase = 0.0  # 0-2π representing time in biological day

        # ── Rhythm Parameters (Based on 24-hour circadian + 90min ultradian) ─────
        self._circadian_period = 24.0 * 3600.0  # 24 hours in seconds
        self._ultradian_period = 90.0 * 60.0    # 90 minutes in seconds
        self._baseline_attention = 0.6
        self._baseline_creativity = 0.5
        self._baseline_energy = 0.6

        # ── Subscribers (Inputs for entrainment) ─────────────────────────────
        # Light/dark cues (simulated)
        self.create_subscription(String, "/grace/sensors/light_exposure",
                                 self._on_light_exposure, 10)
        # Activity/rest cues
        self.create_subscription(String, "/grace/action/activity_level",
                                 self._on_activity_level, 10)
        # Social synchrony cues
        self.create_subscription(String, "/grace/subconscious/social_sync",
                                 self._on_social_sync, 10)

        # ── Publishers (Outputs to other systems) ───────────────────────────
        self._pub = self.create_publisher(String, "/grace/vital/circadian_rhythm", 10)
        self.create_timer(1.0 / self.update_hz, self._update_rhythms)
        self.get_logger().info("Circadian & Ultradian Rhythm ready.")

    # ── Input Processing for Entrainment ────────────────────────────────────
    def _on_light_exposure(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Light exposure helps entrain circadian rhythm
            light_level = data.get("level", 0.5)  # 0=dark, 1=bright
            # Light during subjective day advances clock, at night delays it
            hour_of_day = (self._cycle_phase / (2 * math.pi)) * 24
            if 6 <= hour_of_day <= 18:  # Daytime
                phase_shift = (light_level - 0.5) * 0.1  # Small advance
            else:  # Nighttime
                phase_shift = (light_level - 0.5) * -0.1  # Small delay
            self._cycle_phase += phase_shift
            self._cycle_phase = self._cycle_phase % (2 * math.pi)  # Wrap
        except Exception as e:
            self.get_logger().warn(f"Failed to process light exposure: {e}")

    def _on_activity_level(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Activity level provides zeitgeber (time-giver) cues
            activity = data.get("level", 0.5)  # 0=rest, 1=active
            # High activity during subjective day reinforces rhythm
            hour_of_day = (self._cycle_phase / (2 * math.pi)) * 24
            if 6 <= hour_of_day <= 18:  # Daytime
                reinforcement = (activity - 0.5) * 0.05
                self._cycle_phase += reinforcement
                self._cycle_phase = self._cycle_phase % (2 * math.pi)
        except Exception as e:
            self.get_logger().warn(f"Failed to process activity level: {e}")

    def _on_social_sync(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Social cues help entrain rhythms
            social_sync = data.get("sync_quality", 0.0)  # 0=no sync, 1=perfect sync
            # Strong social synchronization slightly advances phase toward social norm
            if social_sync > 0.7:
                phase_adjustment = (social_sync - 0.7) * 0.02
                self._cycle_phase += phase_adjustment
                self._cycle_phase = self._cycle_phase % (2 * math.pi)
        except Exception as e:
            self.get_logger().warn(f"Failed to process social sync: {e}")

    # ── Rhythm Calculation ────────────────────────────…………………………
    def _update_rhythms(self):
        now = time.time()
        dt = now - self._last_update
        self._last_update = now

        # Natural progression of circadian cycle
        natural_phase_advance = (2 * math.pi * dt) / self._circadian_period
        self._cycle_phase += natural_phase_advance
        self._cycle_phase = self._cycle_phase % (2 * math.pi)  # Wrap around 24-hour cycle

        # Calculate circadian components (0-1 range)
        circadian_phase = self._cycle_phase / (2 * math.pi)  # 0-1 over 24h

        # Core body temperature rhythm (proxy for energy)
        # Peaks in late afternoon, troughs in early morning
        temp_rhythm = 0.5 + 0.3 * math.sin(2 * math.pi * (circadian_phase - 0.25))

        # Cortisol rhythm (attention/alertness)
        # Peaks in early morning, troughs at night
        cortisol_rhythm = 0.3 + 0.4 * math.max(0, math.sin(2 * math.pi * (circadian_phase - 0.2)))

        # Melatonin inverse (creativity often higher in low melatonin)
        # Peaks at night, troughs in morning
        melatonin_rhythm = 0.5 + 0.4 * math.max(0, math.sin(2 * math.pi * (circadian_phase - 0.5)))
        creativity_rhythm = 1.0 - 0.5 * melatonin_rhythm  # Inverse relationship

        # Ultradian rhythms (90-minute cycles) superimposed
        ultradian_phase = (now % self._ultradian_period) / self._ultradian_period  # 0-1
        ultradian_boost = 0.2 * math.sin(2 * math.pi * ultradian_phase)  # +/- 20% modulation

        # Calculate final outputs
        attention = max(0.0, min(1.0,
                    cortisol_rhythm * 0.7 + 0.3 + ultradian_boost * 0.5))
        creativity = max(0.0, min(1.0,
                    creativity_rhythm * 0.6 + 0.4 + ultradian_boost * 0.3))
        energy = max(0.0, min(1.0,
                    temp_rhythm * 0.6 + 0.4 + ultradian_boost * 0.4))

        # Publish rhythm state
        rhythm_state = CircadianRhythm(
            timestamp=now,
            circadian_phase=circadian_phase,
            attention=attention,
            creativity=creativity,
            energy=energy,
            ultradian_phase=ultradian_phase
        )
        out = String()
        out.data = to_json(rhythm_state)
        self._pub.publish(out)

        # Log key transitions occasionally
        if int(now) % 3600 == 0:  # Every hour
            hour_of_day = circadian_phase * 24
            self.get_logger().info(
                f"Rhythm - Hour:{hour_of_day:.1f} "
                f"Att:{attention:.2f} "
                f"Creat:{creativity:.2f} "
                f"Energy:{energy:.2f}"
            )


def main(args=None):
    rclpy.init(args=args)
    node = CircadianRhythmNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()