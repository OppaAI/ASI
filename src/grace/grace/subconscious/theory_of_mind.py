"""
grace_agi/subconscious/theory_of_mind.py
Subconscious Layer — Theory of Mind Stack
Recursive Modeling
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.grace.utils.schemas import TheoryOfMindState, to_json


class TheoryOfMindNode(Node):
    def __init__(self):
        super().__init__("grace_theory_of_mind")

        # ── Parameters ────────────────────────────……………………………………
        self.declare_parameter("update_hz", 0.2)  # Updates every 5 seconds
        self.update_hz = self.get_parameter("update_hz").value

        # ── Internal State ───────────────────────────────────────────────────
        self._tom_level = 0                    # Current depth of recursion (0=none, 1=first order, etc.)
        self._tom_accuracy = 0.6               # Accuracy of our ToM predictions (0-1)
        self._cognitive_load = 0.0             # Current cognitive load from ToM (0-1)
        self._last_update = time.time()
        self._max_tom_level = 5                # Biological limit on recursion depth
        self._base_cost_per_level = 0.1        # Cognitive cost per ToM level

        # ── Theory of Mind Parameters ───────────────────────────────────────
        self._developmental_asymptote = 4.0    # Typical adult ToM ceiling
        self._fatigue_factor = 0.3             # How mental fatigue reduces ToM capacity
        self._motivation_boost = 0.2           # How motivation increases ToM engagement
        self._social_relevance_threshold = 0.3 # Minimum social relevance to engage ToM

        # ── Subscribers (Inputs from other systems) ─────────────────────────
        # Social context that warrants ToM engagement
        self.create_subscription(String, "/grace/subconscious/social_model",
                                 self._on_social_context, 10)
        # Current goals requiring social prediction
        self.create_subscription(String, "/grace/conscious/executive_plan",
                                 self._on_social_goals, 10)
        # Emotional salience of social stimuli
        self.create_subscription(String, "/grace/unconscious/affective_state",
                                 self._on_affective_salience, 10)
        # Cognitive resource availability
        self.create_subscription(String, "/grace/vital/metabolic_resource",
                                 self._on_cognitive_resources, 10)
        # Executive control signals (effort allocation)
        self.create_subscription(String, "/grace/conscious/metacognition",
                                 self._on_executive_control, 10)

        # ── Publishers (Outputs to other systems) ───────────────────────────
        self._pub = self.create_publisher(String, "/grace/subconscious/theory_of_mind_state", 10)
        self.create_timer(1.0 / self.update_hz, self._update_tom)
        self.get_logger().info("Theory of Mind Stack ready.")

    # ── Input Processing ─────────────────────────────────────────────────────
    def _on_social_context(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Social context complexity influences ToM engagement
            social_complexity = data.get("complexity", 0.5)  # 0-1
            num_agents = data.get("agent_count", 1)          # Number of social agents present
            interaction_type = data.get("type", "neutral")   # cooperative, competitive, ambiguous

            # More complex social contexts engage deeper ToM
            context_relevance = social_complexity * min(1.0, num_agents / 5.0)  # Normalize agent count
            self._social_context_relevance = context_relevance
        except Exception as e:
            self.get_logger().warn(f"Failed to process social context: {e}")

    def _on_social_goals(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Goals involving others require ToM
            goal_sociality = data.get("sociality", 0.0)  # 0=solitary  1=purely social
            goal_importance = data.get("priority", 0.5)
            goal_uncertainty = data.get("uncertainty", 0.5)  # How uncertain we are about outcome

            # Goals with high sociality and uncertainty engage ToM
            goal_relevance = goal_sociality * goal_importance * goal_uncertainty
            self._social_goals_relevance = goal_relevance
        except Exception as e:
            self.get_logger().warn(f"Failed to process social goals: {e}")

    def _on_affective_salience(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Emotionally salient social stimuli engage ToM
            social_relevance = data.get("social_relevance", 0.0)  # 0-1
            emotional_intensity = data.get("arousal", 0.3)   # 0-1
            valence_deviation = abs(data.get("valence", 0.5) - 0.5) * 2  # Distance from neutral

            # High arousal + social relevance increases ToM engagement
            affective_relevance = social_relevance * (0.5 + emotional_intensity * 0.5)
            self._affective_salience = affective_relevance
        except Exception as e:
            self.get_logger().warn(f"Failed to process affective salience: {e}")

    def _on_cognitive_resources(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Available cognitive resources limit ToM depth
            glucose = data.get("glucose_equivalent", 1.0)  # 0-1
            ketones = data.get("ketone_level", 0.0)       # 0-1
            effective_fuel = min(1.0, glucose + ketones * 0.7)

            # More fuel allows deeper ToM recursion
            self._cognitive_resource_level = effective_fuel
        except Exception as e:
            self.get_logger().warn(f"Failed to process cognitive resources: {e}")

    def _on_executive_control(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Executive control allocates effort to ToM
            control_effort = data.get("effort_allocation", 0.5)  # 0-1
            control_confidence = data.get("confidence", 0.5)     # 0-1

            # Executive endorsement increases ToM engagement
            self._executive_endorsement = control_effort * control_confidence
        except Exception as e:
            self.getLogger().warn(f"Failed to process executive control: {e}")

    # ── Theory of Mind Dynamics Update ──────────────────────────────────────
    def _update_tom(self):
        now = time.time()
        dt = now - self._last_update
        self._last_update = now

        # Determine target ToM level based on inputs
        # Start with social relevance
        social_relevance = getattr(self, '_social_context_relevance', 0.0)
        social_relevance = max(social_relevance, getattr(self, '_social_goals_relevance', 0.0))
        social_relevance = max(social_relevance, getattr(self, '_affective_salience', 0.0))

        # Apply cognitive resource constraints
        cognitive_limit = getattr(self, '_cognitive_resource_level', 0.5)
        executive_endorsement = getattr(self, '_executive_endorsement', 0.0)
        motivation = getattr(self, '_motivation_boost', 0.2)

        # Calculate available resources for ToM
        available_resources = (cognitive_limit * 0.6) + (executive_endorsement * 0.3) + (motivation * 0.1)
        available_resources = max(0.0, min(1.0, available_resources))

        # Apply fatigue (simplified - in reality would track mental fatigue over time)
        fatigue_factor = getattr(self, '_fatigue_factor', 0.3)
        effective_resources = available_resources * (1.0 - fatigue_factor * 0.5)

        # Map resources to ToM levels (nonlinear - diminishing returns)
        if effective_resources < 0.2:
            target_tom_level = 0
        elif effective_resources < 0.4:
            target_tom_level = 1
        elif effective_resources < 0.6:
            target_tom_level = 2
        elif effective_resources < 0.8:
            target_tom_level = 3
        elif effective_resources < 0.9:
            target_tom_level = 4
        else:
            target_tom_level = 5

        # Apply biological and developmental limits
        max_effective_level = min(self._max_tom_level, self._developmental_asymptote)
        target_tom_level = min(target_mom_level, max_effective_level)

        # Smooth transition toward target level (avoid sudden jumps)
        level_diff = target_tom_level - self._tom_level
        self._tom_level += level_diff * 0.2  # 20% adjustment per update

        # Clamp to valid range
        self._tom_level = max(0.0, min(float(self._max_tom_level), self._tom_level))

        # Calculate cognitive load (increases with ToM depth)
        self._cognitive_load = (self._tom_level / self._max_tom_level) * self._base_cost_per_level * self._tom_level
        self._cognitive_load = max(0.0, min(1.0, self._cognitive_load))

        # Update ToM accuracy based on resources and practice
        # More resources and moderate use improve accuracy; overload decreases it
        practice_factor = min(1.0, self._tom_level / 3.0)  # Optimal around level 3
        overload_penalty = max(0.0, (self._tom_level - 3.0) * 0.1)  # Penalty for excessive levels
        base_accuracy = 0.4 + practice_factor * 0.3  # Baseline improves with practice
        accuracy = base_accuracy - overload_penalty
        self._tom_accuracy = max(0.2, min(0.9, accuracy))

        # Prepare outputs
        tom_state = TheoryOfMindState(
            timestamp=now,
            tom_level=int(self._tom_level),  # Discrete levels
            tom_accuracy=self._tom_accuracy,
            cognitive_load=self._cognitive_load,
            social_relevance=social_relevance,
            cognitive_resources=getattr(self, '_cognitive_resource_level', 0.5),
            executive_endorsement=getattr(self, '_executive_endorsement', 0.0),
            available_resources=effective_resources
        )
        out = String()
        out.data = to_json(tom_state)
        self._pub.publish(out)

        # Log ToM dynamics occasionally
        if int(now) % 10 == 0:  # Every 10 seconds
            self.get_logger().info(
                f"Theory of Mind - Level:{int(self._tom_level)} "
                f"Accuracy:{self._tom_accuracy:.2f} "
                f"Load:{self._cognitive_load:.2f} "
                f"Resources:{effective_resources:.2f}"
            )


def main(args=None):
    rclpy.init(args=args)
    node = TheoryOfMindNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()