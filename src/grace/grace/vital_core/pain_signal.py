"""
grace_agi/vital_core/pain_signal.py
Vital Core — Pain Signal
Conflict Signal: Memory Overload · Goal Violation
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.grace.utils.schemas import PainSignal, to_json


class PainSignalNode(Node):
    def __init__(self):
        super().__init__("grace_pain_signal")

        # ── Parameters ────────────────────────────────────────────────────────
        self.declare_parameter("update_hz", 2.0)  # Fast conflict detection
        self.update_hz = self.get_parameter("update_hz").value

        # ── Internal State ───────────────────────────────────────────────────
        self._pain_level = 0.0          # 0=no pain  1=maximum pain
        self._pain_sources = []         # Track what's causing pain
        self._last_update = time.time()

        # ── Pain Thresholds and Dynamics ────────────────────────────────────
        self._memory_overload_threshold = 0.8  # When memory utilization is high
        self._goal_violation_sensitivity = 0.6 # How sensitive to goal conflicts
        self._pain_decay_rate = 0.1      # How fast pain subsides
        self._recent_events = []        # Track recent conflict events

        # ── Subscribers (Inputs from other systems) ─────────────────────────
        # Memory system load indicators
        self.create_subscription(String, "/grace/subconscious/memory_load",
                                 self._on_memory_load, 10)
        # Goal/prospective memory conflicts
        self.create_subscription(String, "/grace/conflict/goal_violation",
                                 self._on_goal_violation, 10)
        # Cognitive dissonance from hidden workspace
        self.create_subscription(String, "/grace/hidden/cognitive_dissonance",
                                 self._on_dissonance, 10)
        # Error monitoring signals
        self.create_subscription(String, "/grace/hidden/error_monitoring",
                                 self._on_error, 10)

        # ── Publishers (Outputs to other systems) ───────────────────────────
        self._pub = self.create_publisher(String, "/grace/vital/pain_signal", 10)
        self.create_timer(1.0 / self.update_hz, self._update_pain)
        self.get_logger().info("Pain Signal processor ready.")

    # ── Input Processing ─────────────────────────────────────────────────────
    def _on_memory_load(self, msg: String):
        try:
            data = json.loads(msg.data)
            # High memory utilization causes cognitive "pain"
            memory_load = data.get("utilization", 0.0)  # 0-1
            if memory_load > self._memory_overload_threshold:
                overload = (memory_load - self._memory_overload_threshold) / \
                          (1.0 - self._memory_overload_threshold)
                self._add_pain_source("memory_overload", overload * 0.8)
        except Exception as e:
            self.get_logger().warn(f"Failed to process memory load: {e}")

    def _on_goal_violation(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Goal violations create psychological pain
            violation_severity = data.get("severity", 0.0)  # 0-1
            self._add_pain_source("goal_violation", violation_severity * self._goal_violation_sensitivity)
        except Exception as e:
            self.get_logger().warn(f"Failed to process goal violation: {e}")

    def _on_dissonance(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Cognitive dissonance creates psychological discomfort
            dissonance_level = data.get("dissonance", 0.0)  # 0-1
            self._add_pain_source("cognitive_dissonance", dissonance_level * 0.6)
        except Exception as e:
            self.get_logger().warn(f"Failed to process cognitive dissonance: {e}")

    def _on_error(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Errors create frustration/pain
            error_significance = data.get("significance", 0.0)  # 0-1
            self._add_pain_source("processing_error", error_significance * 0.5)
        except Exception as e:
            self.get_logger().warn(f"Failed to process error signal: {e}")

    def _add_pain_source(self, source: str, intensity: float):
        """Add or update a pain source with decay"""
        # Remove old instances of this source
        self._pain_sources = [s for s in self._pain_sources if s['source'] != source]
        # Add new instance with timestamp
        self._pain_sources.append({
            'source': source,
            'intensity': max(0.0, min(1.0, intensity)),
            'timestamp': time.time()
        })

    # ── Pain Dynamics Update ────────────────────────────────────────────────
    def _update_pain(self):
        now = time.time()
        self._last_update = now

        # Decay old pain sources (older than 10 seconds fade out)
        cutoff_time = now - 10.0
        self._pain_sources = [
            s for s in self._pain_sources
            if s['timestamp'] > cutoff_time
        ]

        # Calculate total pain from all active sources
        if self._pain_sources:
            # Use maximum intensity (winner-takes-most for pain)
            max_intensity = max(s['intensity'] for s in self._pain_sources)
            # Add some contribution from multiple sources
            total_from_sources = sum(s['intensity'] for s in self._pain_sources)
            combined_pain = min(1.0, max_intensity + 0.3 * (total_from_sources - max_intensity))
            self._pain_level = combined_pain
        else:
            # Pain naturally decays toward zero
            self._pain_level = max(0.0, self._pain_level - self._pain_decay_rate * 0.1)

        # Publish pain signal
        pain_signal = PainSignal(
            timestamp=now,
            pain_intensity=self._pain_level,
            pain_sources=[s['source'] for s in self._pain_sources],
            sources_detail={s['source']: s['intensity'] for s in self._pain_sources}
        )
        out = String()
        out.data = to_json(pain_signal)
        self._pub.publish(out)

        # Log significant pain events
        if self._pain_level > 0.5 and int(now) % 10 == 0:  # Every 10 seconds when in pain
            sources_str = ", ".join([s['source'] for s in self._pain_sources[-3:]])  # Last 3
            self.get_logger().warn(
                f"Pain Signal: {self._pain_level:.2f} (sources: {sources_str})"
            )


def main(args=None):
    rclpy.init(args=args)
    node = PainSignalNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()