"""
grace_agi/vital_core/drive.py
Vital Core — Homeostatic Drive Loop
Implements core biological drives: Energy, Curiosity, Patience Decay
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.grace.utils.schemas import HomeostaticDriveState, to_json


class DriveNode(Node):
    def __init__(self):
        super().__init__("grace_drive")

        # ── Parameters ────────────────────────────────────────────────────────
        self.declare_parameter("update_hz", 0.1)  # Slow biological timescale
        self.update_hz = self.get_parameter("update_hz").value

        # ── Internal State (Biological Drives) ───────────────────────────────
        self._energy_level = 1.0      # 0=depleted, 1=optimal
        self._curiosity_level = 0.7   # 0=no interest, 1=highly curious
        self._patience_level = 0.8    # 0=impulsive, 1=patient
        self._last_update = time.time()

        # ── Drive Dynamics Parameters ───────────────────────────────────────
        self._energy_decay_rate = 0.01      # per second at rest
        self._curiosity_boost_rate = 0.005  # novelty increases curiosity
        self._patience_decay_rate = 0.002   # frustration reduces patience
        self._baseline_energy = 0.6
        self._baseline_curiosity = 0.7
        self._baseline_patience = 0.8

        # ── Subscribers (Input from other systems) ─────────────────────────
        # Energy input from metabolic processes
        self.create_subscription(String, "/grace/vital/metabolic_state",
                                 self._on_metabolic_state, 10)
        # Curiosity input from novelty detection
        self.create_subscription(String, "/grace/unconscious/surprise_novelty",
                                 self._on_novelty, 10)
        # Patience input from conflict resolution
        self.create_subscription(String, "/grace/vital/conflict_signal",
                                 self._on_conflict, 10)

        # ── Publishers (Output to other systems) ───────────────────────────
        self._pub = self.create_publisher(String, "/grace/vital/drive_state", 10)
        self.create_timer(1.0 / self.update_hz, self._update_drives)
        self.get_logger().info("Homeostatic Drive Loop ready.")

    # ── Input Processing ─────────────────────────────────────────────────────
    def _on_metabolic_state(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Metabolic state affects energy levels
            metabolic_energy = data.get("energy_level", 0.5)
            # Blend current energy with metabolic input
            self._energy_level = 0.7 * self._energy_level + 0.3 * metabolic_energy
        except Exception as e:
            self.get_logger().warn(f"Failed to process metabolic state: {e}")

    def _on_novelty(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Novelty boosts curiosity
            novelty_score = data.get("surprise", 0.0)
            self._curiosity_level = min(1.0, self._curiosity_level +
                                       novelty_score * self._curiosity_boost_rate)
        except Exception as e:
            self.get_logger().warn(f"Failed to process novelty: {e}")

    def _on_conflict(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Conflict reduces patience
            conflict_level = data.get("conflict_intensity", 0.0)
            self._patience_level = max(0.0, self._patience_level -
                                      conflict_level * self._patience_decay_rate)
        except Exception as e:
            self.get_logger().warn(f"Failed to process conflict signal: {e}")

    # ── Drive Dynamics Update ────────────────────────────────────────────────
    def _update_drives(self):
        now = time.time()
        dt = now - self._last_update
        self._last_update = now

        # Energy: Natural decay toward baseline, bounded [0,1]
        energy_target = self._baseline_energy
        if self._energy_level > energy_target:
            self._energy_level -= self._energy_decay_rate * dt
        else:
            self._energy_level += self._energy_decay_rate * dt * 0.5  # Slower recovery
        self._energy_level = max(0.0, min(1.0, self._energy_level))

        # Curiosity: Slow decay toward baseline with novelty boosts
        if self._curiosity_level > self._baseline_curiosity:
            self._curiosity_level -= self._curiosity_boost_rate * dt * 0.5
        else:
            self._curiosity_level += self._curiosity_boost_rate * dt * 0.2
        self._curiosity_level = max(0.0, min(1.0, self._curiosity_level))

        # Patience: Slow recovery toward baseline when no conflict
        if self._patience_level < self._baseline_patience:
            self._patience_level += self._patience_decay_rate * dt * 0.3
        else:
            self._patience_level -= self._patience_decay_rate * dt * 0.1
        self._patience_level = max(0.0, min(1.0, self._patience_level))

        # Publish drive state
        drive_state = HomeostaticDriveState(
            energy_level=self._energy_level,
            curiosity_level=self._curiosity_level,
            patience_level=self._patience_level,
            timestamp=now
        )
        out = String()
        out.data = to_json(drive_state)
        self._pub.publish(out)

        # Log occasionally for monitoring
        if int(now) % 30 == 0:  # Every 30 seconds
            self.get_logger().info(
                f"Drives - E:{self._energy_level:.2f} "
                f"C:{self._curiosity_level:.2f} "
                f"P:{self._patience_level:.2f}"
            )


def main(args=None):
    rclpy.init(args=args)
    node = DriveNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()