"""
grace_agi/dreaming/neuroplasticity.py
Non-SLM node — Neuroplasticity.
Models synaptic pruning and growth analogues with long-term potentiation
for strengthening connections based on frequency and recency.
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String

from grace.utils.schemas import NeuroplasticityState, to_json


class NeuroplasticityNode(Node):
    def __init__(self):
        super().__init__("grace_neuroplasticity")

        self.declare_parameter("update_hz", 10.0)
        hz = self.get_parameter("update_hz").value

        self._consolidation_trigger: dict = {}
        self._distillation_buffer: list[dict] = []
        self._connection_strength: dict[str, float] = {}
        self._connection_age: dict[str, float] = {}
        self._pruning_threshold: float = 0.15
        self._growth_factor: float = 0.05
        self._plasticity_active: bool = False
        self._cycle: int = 0

        self.create_subscription(String, "/grace/dreaming/consolidation",
                                 self._on_consolidation, 10)
        self.create_subscription(String, "/grace/dreaming/distillation",
                                 self._on_distillation, 10)

        self._pub = self.create_publisher(String, "/grace/dreaming/neuroplasticity", 10)
        self.create_timer(1.0 / hz, self._process)
        self.get_logger().info("Neuroplasticity ready.")

    def _on_consolidation(self, msg: String):
        try:
            self._consolidation_trigger = json.loads(msg.data)
        except Exception:
            pass

    def _on_distillation(self, msg: String):
        try:
            self._distillation_buffer.append(json.loads(msg.data))
            if len(self._distillation_buffer) > 20:
                self._distillation_buffer.pop(0)
        except Exception:
            pass

    def _region_for_insight(self, insight: str) -> str:
        insight_lower = insight.lower()
        if any(w in insight_lower for w in ["moral", "ethic", "right", "wrong"]):
            return "conscience"
        if any(w in insight_lower for w in ["social", "person", "friend"]):
            return "social_cognition"
        if any(w in insight_lower for w in ["memory", "remember", "past"]):
            return "hippocampal"
        if any(w in insight_lower for w in ["plan", "goal", "future"]):
            return "prefrontal"
        if any(w in insight_lower for w in ["emotion", "feel", "fear"]):
            return "amygdala"
        return "cortical_association"

    def _process(self):
        self._cycle += 1
        now = time.time()

        new_insights = self._consolidation_trigger.get("insights", [])
        personality_deltas = self._consolidation_trigger.get("personality_deltas", {})
        has_trigger = bool(new_insights or personality_deltas)

        for pkt in self._distillation_buffer:
            for insight in pkt.get("insights", []):
                if insight not in self._connection_strength:
                    self._connection_strength[insight] = 0.1
                    self._connection_age[insight] = now

        for insight in new_insights:
            if insight not in self._connection_strength:
                self._connection_strength[insight] = 0.1
                self._connection_age[insight] = now

        if has_trigger:
            self._plasticity_active = True
            for insight in new_insights:
                self._connection_strength[insight] = min(1.0,
                    self._connection_strength.get(insight, 0.0) + self._growth_factor)
                self._connection_age[insight] = now

        for key in list(self._connection_strength.keys()):
            age = now - self._connection_age.get(key, now)
            decay = age / 3600.0 * 0.01
            self._connection_strength[key] = max(0.0,
                self._connection_strength.get(key, 0.0) - decay)

        pruned = 0
        total_prune_intensity = 0.0
        for key in list(self._connection_strength.keys()):
            strength = self._connection_strength[key]
            if strength < self._pruning_threshold:
                total_prune_intensity += strength
                del self._connection_strength[key]
                del self._connection_age[key]
                pruned += 1

        growth = 0.0
        target_region = "cortical_association"
        for key, strength in self._connection_strength.items():
            if strength > 0.8:
                growth += strength * 0.1
                target_region = self._region_for_insight(key)

        pruned_intensity = min(1.0, total_prune_intensity * 0.1)
        growth_intensity = min(1.0, growth)
        ltp = min(1.0, len([s for s in self._connection_strength.values() if s > 0.7]) * 0.1)

        if self._plasticity_active or self._cycle % 10 == 0:
            state = NeuroplasticityState(
                plasticity_active=self._plasticity_active or pruned > 0,
                pruning_intensity=pruned_intensity,
                growth_intensity=growth_intensity,
                target_region=target_region,
                long_term_potentiation=ltp,
                structural_change=(
                    f"Pruned {pruned} weak connections, "
                    f"strengthened {len([s for s in self._connection_strength.values() if s > 0.7])} pathways "
                    f"in {target_region}" if pruned or growth > 0 else "No structural change"),
            )
            out = String(); out.data = to_json(state)
            self._pub.publish(out)

            if pruned > 0 or growth > 0:
                self.get_logger().info(
                    f"Plasticity: pruned {pruned}, growth {growth_intensity:.2f}, "
                    f"LTP {ltp:.2f} in {target_region}")

        self._plasticity_active = False
        self._consolidation_trigger = {}


def main(args=None):
    rclpy.init(args=args)
    node = NeuroplasticityNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
