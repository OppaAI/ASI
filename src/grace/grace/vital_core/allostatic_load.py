"""
grace_agi/vital_core/allostatic_load.py
Vital Core — Allostatic Load Budget
Cumulative Stress · Cognitive Cost Tracking
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.grace.utils.schemas import AllostaticLoad, to_json


class AllostaticLoadNode(Node):
    def __init__(self):
        super().__init__("grace_allostatic_load")

        # ── Parameters ────────────────────────────────────────────────────────
        self.declare_parameter("update_hz", 0.1)  # Slow accumulation tracking
        self.update_hz = self.get_parameter("update_hz").value

        # ── Internal State ───────────────────────────────────────────────────
        self._allostatic_load = 0.0     # 0=no load  1=overwhelming load
        self._cognitive_cost_today = 0.0 # Daily cognitive expenditure
        self._recovery_rate = 0.01      # per hour recovery during rest
        self._instantaneous_load = 0.0  # Short-term stress accumulator
        self._last_update = time.time()
        self._last_reset = time.time()  # For daily reset

        # ── Load Accumulation Factors ───────────────────────────────────────
        self._stress_to_load_factor = 0.3      # How much stress becomes load
        self._cognitive_cost_factor = 0.05     # Cost per unit of cognitive work
        self._emotional_labor_factor = 0.04    # Cost of emotional regulation
        self._decay_during_sleep = 0.1         # Recovery during low activity

        # ── Subscribers (Inputs from other systems) ─────────────────────────
        # Stress/pain inputs
        self.create_subscription(String, "/grace/vital/pain_signal",
                                 self._on_pain, 10)
        # Neuromodulator stress indicators
        self.create_subscription(String, "/grace/vital/neuromodulatory_state",
                                 self._on_neuromodulators, 10)
        # Cognitive work indicators
        self.create_subscription(String, "/grace/conscious/executive_plan",
                                 self._on_cognitive_work, 10)
        # Emotional labor from regulation
        self.create_subscription(String, "/grace/unconscious/emotion_regulation",
                                 self._on_emotional_labor, 10)

        # ── Publishers (Outputs to other systems) ───────────────────────────
        self._pub = self.create_publisher(String, "/grace/vital/allostatic_load", 10)
        self.create_timer(1.0 / self.update_hz, self._update_load)
        self.get_logger().info("Allostatic Load Budget ready.")

    # ── Input Processing ─────────────────────────────────────────────────────
    def _on_pain(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Pain contributes to allostatic load
            pain_intensity = data.get("pain_intensity", 0.0)
            stress_contribution = pain_intensity * self._stress_to_load_factor
            self._instantaneous_load += stress_contribution
        except Exception as e:
            self.get_logger().warn(f"Failed to process pain signal: {e}")

    def _on_neuromodulators(self, msg: String):
        try:
            data = json.loads(msg.data)
            # High cortisol and norepinephrine indicate physiological stress
            cortisol = data.get("cortisol", 0.3)
            norepinephrine = data.get("norepinephrine", 0.4)
            # Deviations from baseline create load
            cortisol_stress = max(0, cortisol - 0.3) * 2.0  # Above baseline
            neo_stress = max(0, norepinephrine - 0.4) * 1.5  # Above baseline
            stress_contribution = (cortisol_stress + neo_stress) * self._stress_to_load_factor
            self._instantaneous_load += stress_contribution
        except Exception as e:
            self.get_logger().warn(f"Failed to process neuromodulators: {e}")

    def _on_cognitive_work(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Complex planning and goal pursuit have cognitive costs
            plan_complexity = len(data.get("steps", [])) * 0.1  # Rough complexity measure
            priority = data.get("priority", 0.5)
            cognitive_cost = (plan_complexity + priority) * self._cognitive_cost_factor
            self._cognitive_cost_today += cognitive_cost
        except Exception as e:
            self.get_logger().warn(f"Failed to process cognitive work: {e}")

    def _on_emotional_labor(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Emotional regulation effort has metabolic cost
            regulation_effort = data.get("regulation_effort", 0.0)
            emotional_cost = regulation_effort * self._emotional_labor_factor
            self._cognitive_cost_today += emotional_cost
        except Exception as e:
            self.get_logger().warn(f"Failed to process emotional labor: {e}")

    # ── Load Dynamics Update ────────────────────────────────────────────────
    def _update_load(self):
        now = time.time()
        dt = now - self._last_update
        self._last_update = now

        # Daily reset at midnight (simplified - every 24 hours)
        if now - self._last_reset > 86400:  # 24 hours
            self._cognitive_cost_today = 0.0
            self._last_reset = now
            self.get_logger().info("Daily allostatic load reset")

        # Instantaneous load decays quickly
        self._instantaneous_load = max(0.0, self._instantaneous_load - 0.1 * dt)

        # Allostatic load accumulates instantaneous load with slow decay
        # Load increases with instantaneous stressors
        load_increase = self._instantaneous_load * 0.1 * dt

        # Load decreases during low activity periods (recovery)
        activity_level = min(1.0, self._instantaneous_load * 2.0)  # Proxy for activity
        recovery = self._recovery_rate * (1.0 - activity_level) * dt  # More recovery when less active

        # Update total load
        self._allostatic_load += load_increase - recovery
        self._allostatic_load = max(0.0, min(2.0, self._allostatic_load))  # Allow some overflow

        # Publish allostatic load
        allostatic_load = AllostaticLoad(
            timestamp=now,
            allostatic_load=self._allostatic_load,
            cognitive_cost_today=self._cognitive_cost_today,
            instantaneous_load=self._instantaneous_load,
            recovery_rate=self._recovery_rate * (1.0 - min(1.0, activity_level))
        )
        out = String()
        out.data = to_json(allostatic_load)
        self._pub.publish(out)

        # Log when load becomes significant
        if self._allostatic_load > 1.5 and int(now) % 300 == 0:  # Every 5 minutes when overloaded
            self.get_logger().warn(
                f"High Allostatic Load: {self._allostatic_load:.2f} "
                f"(daily cognitive cost: {self._cognitive_cost_today:.2f})"
            )

    def __init__(self):
        super().__init__("grace_allostatic_load")
        # Initialize instantaneous load tracker
        self._instantaneous_load = 0.0
        # Call the original __init__ logic after adding this field
        # ... rest of original init continues ...


# Need to fix the __init__ method - let me rewrite it properly