"""
grace_agi/vital_core/metabolic_tracker.py
Vital Core — Metabolic Resource Tracker
Cognitive Glucose Analogue · Depletion under Load
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.grace.utils.schemas import MetabolicResource, to_json


class MetabolicTrackerNode(Node):
    def __init__(self):
        super().__init__("grace_metabolic_tracker")

        # ── Parameters ────────────────────────────────────────────────────────
        self.declare_parameter("update_hz", 0.5)  # Update twice per second
        self.update_hz = self.get_parameter("update_hz").value

        # ── Internal State ───────────────────────────────────────────────────
        self._glucose_equivalent = 1.0    # 0=depleted  1=optimal (cognitive fuel)
        self._ketone_level = 0.0          # Alternative fuel during fasting
        self._lactate_level = 0.0         # Byproduct of intense activity
        self._last_update = time.time()
        self._basal_consumption = 0.01    # Base metabolic rate per second

        # ── Resource Dynamics Parameters ─────────────────────────────────────
        self._glucose_storage_capacity = 1.0   # Normal storage
        self._glucose_replenish_rate = 0.02    # From food/internal stores per sec
        self._ketone_production_threshold = 0.3 # Start ketones when low glucose
        self._lactate_clearance_rate = 0.05    # Clear lactate during rest

        # ── Subscribers (Inputs from cognitive activity) ─────────────────────
        # Cognitive work consumption
        self.create_subscription(String, "/grace/conscious/executive_plan",
                                 self._on_cognitive_work, 10)
        # Working memory load
        self.create_subscription(String, "/grace/conscious/working_memory",
                                 self._on_working_memory, 10)
        # Global workspace activation
        self.create_subscription(String, "/grace/conscious/global_workspace",
                                 self._on_global_workspace, 10)
        # Emotional processing (limbic system activity)
        self.create_subscription(String, "/grace/unconscious/affective_state",
                                 self._on_emotional_processing, 10)

        # ── Publishers (Outputs to other systems) ───────────────────────────
        self._pub = self.create_publisher(String, "/grace/vital/metabolic_resource", 10)
        self.create_timer(1.0 / self.update_hz, self._update_resources)
        self.get_logger().info("Metabolic Resource Tracker ready.")

    # ── Input Processing (Resource Consumption) ─────────────────────────────
    def _on_cognitive_work(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Executive function planning consumes glucose
            plan_complexity = len(data.get("steps", [])) * 0.1
            priority = data.get("priority", 0.5)
            cognitive_load = (plan_complexity + priority) * 0.5  # 0-1 scale
            consumption = cognitive_load * 0.03  # Glucose per unit work
            self._glucose_equivalent = max(0.0, self._glucose_equivalent - consumption)
            # Lactate byproduct of intense processing
            if cognitive_load > 0.7:
                lactate_production = (cognitive_load - 0.7) * 0.02
                self._lactate_level = min(1.0, self._lactate_level + lactate_production)
        except Exception as e:
            self.get_logger().warn(f"Failed to process cognitive work: {e}")

    def _on_working_memory(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Working memory maintenance consumes resources
            load = data.get("utilization", 0.0)  # 0-1
            consumption = load * 0.02
            self._glucose_equivalent = max(0.0, self._glucose_equivalent - consumption)
        except Exception as e:
            self.get_logger().warn(f"Failed to process working memory: {e}")

    def _on_global_workspace(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Global workspace activation (conscious processing) is expensive
            activation_level = data.get("salience", 0.0)  # 0-1
            consumption = activation_level * 0.04
            self._glucose_equivalent = max(0.0, self._glucose_equivalent - consumption)
        except Exception as e:
            self.get_logger().warn(f"Failed to process global workspace: {e}")

    def _on_emotional_processing(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Emotional processing (amygdala, etc.) consumes resources
            arousal = data.get("arousal", 0.0)  # 0-1
            valence_intensity = abs(data.get("valence", 0.5) - 0.5) * 2  # Distance from neutral
            emotional_load = (arousal + valence_intensity) / 2
            consumption = emotional_load * 0.025
            self._glucose_equivalent = max(0.0, self._glucose_equivalent - consumption)
        except Exception as e:
            self.get_logger().warn(f"Failed to process emotional processing: {e}")

    # ── Resource Dynamics Update ───────────────────────────────────────────
    def _update_resources(self):
        now = time.time()
        dt = now - self._last_update
        self._last_update = now

        # Basal consumption (always running)
        basal_consumption = self._basal_consumption * dt
        self._glucose_equivalent = max(0.0, self._glucose_equivalent - basal_consumption)

        # Glucose replenishment (from stores or intake)
        if self._glucose_equivalent < 0.8:  # Not full
            replenish_amount = self._glucose_replenish_rate * dt
            # Replenishment slows as stores fill
            replenish_amount *= (1.0 - self._glucose_equivalent)
            self._glucose_equivalent = min(self._glucose_storage_capacity,
                                         self._glucose_equivalent + replenish_amount)

        # Ketone production during low glucose (alternative fuel)
        if self._glucose_equivalent < self._ketone_production_threshold:
            # Produce ketones as alternative fuel
            ketone_deficit = self._ketone_production_threshold - self._glucose_equivalent
            ketone_production = ketone_deficit * 0.01 * dt
            self._ketone_level = min(0.5, self._ketone_level + ketone_production)
            # Ketones can partially substitute for glucose
            glucose_equivalent_from_ketones = self._ketone_level * 0.7
            effective_glucose = self._glucose_equivalent + glucose_equivalent_from_ketones
        else:
            # Clear ketones when glucose is sufficient
            self._ketone_level = max(0.0, self._ketone_level - 0.005 * dt)
            effective_glucose = self._glucose_equivalent

        # Lactate clearance during rest
        if self._lactate_level > 0.1:
            clearance = self._lactate_clearance_rate * dt
            self._lactate_level = max(0.0, self._lactate_level - clearance)

        # Publish metabolic state
        metabolic_state = MetabolicResource(
            timestamp=now,
            glucose_equivalent=self._glucose_equivalent,
            ketone_level=self._ketone_level,
            lactate_level=self._lactate_level,
            effective_glucose=min(1.0, self._glucose_equivalent + self._ketone_level * 0.7)
        )
        out = String()
        out.data = to_json(metabolic_state)
        self._pub.publish(out)

        # Warn when resources are low
        if effective_glucose < 0.3 and int(now) % 10 == 0:  # Every 10 seconds when low
            self.get_logger().warn(
                f"Low Cognitive Fuel: Glu={self._glucose_equivalent:.2f} "
                f"Ket={self._ketone_level:.2f} "
                f"Lac={self._lactate_level:.2f}"
            )


def main(args=None):
    rclpy.init(args=args)
    node = MetabolicTrackerNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()