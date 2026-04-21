"""
grace_agi/subconscious/moral_disgust_memory.py
Subconscious Layer — Moral Disgust Memory
Moral Contamination · Purification Motivation · Restitution Drive
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.grace.utils.schemas import MoralDisgustMemoryState, to_json


class MoralDisgustMemoryNode(Node):
    def __init__(self):
        super().__init__("grace_moral_disgust_memory")

        # ── Parameters ────────────────────────────────────────────────────────
        self.declare_parameter("update_hz", 0.1)  # Updates every 10 seconds
        self.update_hz = self.get_parameter("update_hz").value

        # ── Internal State ───────────────────────────────────────────────────
        self._contamination_sensitivity = 0.5  # 0=low sensitivity  1=high sensitivity to moral contamination
        self._contamination_history = 0.3      # 0=no history  1=extensive contamination history
        self._purification_motivation = 0.4    # 0=no motivation  1=strong motivation to purify
        self._moral_purity_ideal = 0.7         # 0=low standards  1=high moral purity standards
        self._contamination_avoidance = 0.6    # 0=no avoidance  1=strong avoidance of contaminants
        self._guilt_response = 0.2             # 0=no guilt  1=strong guilt response
        self._shame_response = 0.3             # 0=no shame  1=strong shame response
        self._restitution_drive = 0.5          # 0=no restitution  1=strong drive to make restitution
        self._forgiveness_capacity = 0.6       # 0=no forgiveness  1=high capacity for forgiveness
        self._last_update = time.time()

        # ── Moral Disgust Memory Parameters ───────────────────────────────
        self._memory_decay_rate = 0.005        # How fast contamination memories fade
        self._sensitivity_growth_rate = 0.01   # How sensitivity increases with exposure
        self._ideal_decay_rate = 0.002         # How purity ideals decay without reinforcement
        self._avoidance_learning = 0.015       # How avoidance increases with experience
        self._guilt_shame_ratio = 0.6          # Ratio of guilt to shame responses (0=all shame, 1=all guilt)
        self._restitution_threshold = 0.4      # Contamination level needed to trigger restitution
        self._forgiveness_growth = 0.008       # How forgiveness capacity grows with time

        # ── Subscribers (Inputs from other systems) ─────────────────────────
        # Moral violations detected by conscience
        self.create_subscription(String, "/grace/conscience/moral_violation",
                                 self._on_moral_violation, 10)
        # Purity violations from sensory/social systems
        self.create_subscription(String, "/grace/perception/purity_violation",
                                 self._on_purity_violation, 10)
        # Social transgressions from social systems
        self.create_subscription(String, "/grace/social/transgression",
                                 self._on_social_transgression, 10)
        # Restitution actions taken
        self.create_subscription(String, "/grace/action/restitution_completed",
                                 self._on_restitution_completed, 10)
        # Forgiveness experiences
        self.create_subscription(String, "/grace/social/forgiveness_received",
                                 self._on_forgiveness_received, 10)
        # Moral teachings and ideals
        self.create_subscription(String, "/grace/conscience/moral_teaching",
                                 self._on_moral_teaching, 10)

        # ── Publishers (Outputs to other systems) ───────────────────────────
        self._pub = self.create_publisher(String, "/grace/subconscious/moral_disgust_memory_state", 10)
        self.create_timer(1.0 / self.update_hz, self._update_moral_disgust_memory)
        self.get_logger().info("Moral Disgust Memory ready.")

    # ── Input Processing ─────────────────────────────────────────────────────
    def _on_moral_violation(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Moral violations increase contamination history and sensitivity
            violation_severity = data.get("severity", 0.0)    # 0=minor  1=severe violation
            violation_intentional = data.get("intentional", 0.5) # 0=accidental  1=intentional
            violation_public = data.get("public", 0.3)        # 0=private  1=public knowledge

            # Increase contamination history
            history_increase = violation_severity * violation_intentional * 0.2
            self._contamination_history = min(1.0, self._contamination_history + history_increase)

            # Intentional violations increase sensitivity more
            sensitivity_increase = violation_severity * violation_intentional * self._sensitivity_growth_rate
            self._contamination_sensitivity = min(1.0, self._contamination_sensitivity + sensitivity_increase)

            # Public violations increase avoidance motivation
            if violation_public > 0.5:
                avoidance_increase = violation_severity * violation_public * 0.15
                self._contamination_avoidance = min(1.0, self._contamination_avoidance + avoidance_increase)

            # Violations increase guilt/shame responses
            moral_emotion_increase = violation_severity * 0.1
            guilt_increase = moral_emotion_increase * self._guilt_shame_ratio
            shame_increase = moral_emotion_increase * (1.0 - self._guilt_shame_ratio)
            self._guilt_response = min(1.0, self._guilt_response + guilt_increase)
            self._shame_response = min(1.0, self._shame_response + shame_increase)

            # High severity violations increase purification motivation
            if violation_severity > 0.6:
                purification_increase = (violation_severity - 0.6) * 0.3
                self._purification_motivation = min(1.0, self._purification_motivation + purification_increase)

        except Exception as e:
            self.get_logger().warn(f"Failed to process moral violation: {e}")

    def _on_purity_violation(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Purity violations (physical/social) affect moral contamination system
            violation_level = data.get("violation_level", 0.0)  # 0=clean  1=contaminated
            contamination_type = data.get("type", "physical")   # physical, social, moral
            source_proximity = data.get("proximity", 0.5)       # How close the source was

            # Physical/social contamination affects moral contamination sensitivity
            if contamination_type in ["physical", "social"]:
                sensitivity_increase = violation_level * source_proximity * 0.05
                self._contamination_sensitivity = min(1.0, self._contamination_sensitivity + sensitivity_increase)

                # Contamination increases avoidance motivation
                avoidance_increase = violation_level * source_proximity * 0.1
                self._contamination_avoidance = min(1.0, self._contamination_avoidance + avoidance_increase)

                # Contamination increases purification motivation
                purification_increase = violation_level * source_proximity * 0.15
                self._purification_motivation = min(1.0, self._purification_motivation + purification_increase)

                # Contamination increases guilt/shame if perceived as moral failing
                if contamination_type == "social" or source_proximity > 0.7:
                    emotion_increase = violation_level * source_proximity * 0.08
                    guilt_increase = emotion_increase * self._guilt_shame_ratio
                    shame_increase = emotion_increase * (1.0 - self._guilt_shame_ratio)
                    self._guilt_response = min(1.0, self._guilt_response + guilt_increase)
                    self._shame_response = min(1.0, self._shame_response + shame_increase)

        except Exception as e:
            self.get_logger().warn(f"Failed to process purity violation: {e}")

    def _on_social_transgression(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Social transgressions contribute to moral contamination
            transgression_severity = data.get("severity", 0.0)    # 0=minor  1=severe
            social_impact = data.get("social_impact", 0.5)       # Impact on social relationships
            repair_possible = data.get("repair_possible", 0.5)    # Whether repair is possible

            # Social transgressions increase contamination history
            history_increase = transgression_severity * social_impact * 0.15
            self._contamination_history = min(1.0, self._contamination_history + history_increase)

            # Unrepairable transgressions increase contamination sensitivity
            if repair_possible < 0.3:
                sensitivity_increase = transgression_severity * (1.0 - repair_possible) * 0.1
                self._contamination_sensitivity = min(1.0, self._contamination_sensitivity + sensitivity_increase)

            # Transgressions increase avoidance of similar situations
            avoidance_increase = transgression_severity * social_impact * 0.1
            self._contamination_avoidance = min(1.0, self._contamination_avoidance + avoidance_increase)

            # Transgressions increase guilt/shame responses
            emotion_increase = transgression_severity * social_impact * 0.1
            guilt_increase = emotion_increase * self._guilt_shame_ratio
            shame_increase = emotion_increase * (1.0 - self._guilt_shame_ratio)
            self._guilt_response = min(1.0, self._guilt_response + guilt_increase)
            self._shame_response = min(1.0, self._shame_response + shame_increase)

        except Exception as e:
            self.get_logger().warn(f"Failed to process social transgression: {e}")

    def _on_restitution_completed(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Completed restitution reduces contamination history and increases forgiveness
            restitution_effectiveness = data.get("effectiveness", 0.5)  # How effective restitution was
            restitution_completeness = data.get("completeness", 0.5)    # How complete restitution was
            victim_forgiveness = data.get("victim_forgiveness", 0.5)    # Whether victim forgave

            # Effective restitution reduces contamination history
            history_reduction = restitution_effectiveness * restitution_completeness * 0.2
            self._contamination_history = max(0.0, self._contamination_history - history_reduction)

            # Restitution increases forgiveness capacity (learning that repair works)
            forgiveness_increase = restitution_effectiveness * restitution_completeness * 0.1
            self._forgiveness_capacity = min(1.0, self._forgiveness_capacity + forgiveness_increase)

            # Successful restitution reduces guilt/shame
            guilt_reduction = restitution_effectiveness * restitution_completeness * 0.15
            shame_reduction = restitution_effectiveness * restitution_completeness * 0.1
            self._guilt_response = max(0.0, self._guilt_response - guilt_reduction)
            self._shame_response = max(0.0, self._shame_response - shame_reduction)

            # Victim forgiveness increases motivation for future restitution
            if victim_forgiveness > 0.5:
                restitution_motivation_increase = victim_forgiveness * 0.2
                self._restitution_drive = min(1.0, self._restitution_drive + restitution_motivation_increase)

        except Exception as e:
            self.get_logger().warn(f"Failed to process restitution completed: {e}")

    def _on_forgiveness_received(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Forgiveness received increases forgiveness capacity and reduces contamination
            forgiveness_amount = data.get("amount", 0.0)    # 0=no forgiveness  1=complete forgiveness
            forgiveness_sincerity = data.get("sincerity", 0.5) # How sincere the forgiveness is
            relationship_value = data.get("relationship_value", 0.5) # Value of the relationship

            # Forgiveness increases forgiveness capacity
            forgiveness_increase = forgiveness_amount * forgiveness_sincerity * self._forgiveness_growth
            self._forgiveness_capacity = min(1.0, self._forgiveness_capacity + forgiveness_increase)

            # Forgiveness reduces contamination history (moral cleansing)
            history_reduction = forgiveness_amount * forgiveness_sincerity * 0.15
            self._contamination_history = max(0.0, self._contamination_history - history_reduction)

            # Forgiveness reduces guilt/shame responses
            guilt_reduction = forgiveness_amount * forgiveness_sincerity * 0.2
            shame_reduction = forgiveness_amount * forgiveness_sincerity * 0.1
            self._guilt_response = max(0.0, self._guilt_response - guilt_reduction)
            self._shame_response = max(0.0, self._shame_response - shame_reduction)

            # Forgiveness increases motivation to make restitution (reciprocity norm)
            restitution_increase = forgiveness_amount * forgiveness_sincerity * relationship_value * 0.1
            self._restitution_drive = min(1.0, self._restitution_drive + restitution_increase)

        except Exception as e:
            self.get_logger().warn(f"Failed to process forgiveness received: {e}")

    def _on_moral_teaching(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Moral teachings affect purity ideals and sensitivity
            teaching_strength = data.get("strength", 0.5)     # How strong/impactful the teaching is
            teaching_clarity = data.get("clarity", 0.5)       # How clear/unambiguous the teaching is
            teaching_relevance = data.get("relevance", 0.5)   # How relevant to current life

            # Strong, clear teachings increase moral purity ideals
            ideal_increase = teaching_strength * teaching_clarity * teaching_relevance * 0.1
            self._moral_purity_ideal = min(1.0, self._moral_purity_ideal + ideal_increase)

            # Teachings about contamination increase sensitivity
            contamination_focus = data.get("contamination_focus", 0.0) # Focus on contamination aspects
            if contamination_focus > 0.5:
                sensitivity_increase = teaching_strength * teaching_clarity * contamination_focus * 0.1
                self._contamination_sensitivity = min(1.0, self._contamination_sensitivity + sensitivity_increase)

            # Teachings about forgiveness increase forgiveness capacity
            forgiveness_focus = data.get("forgiveness_focus", 0.0) # Focus on forgiveness aspects
            if forgiveness_focus > 0.5:
                forgiveness_increase = teaching_strength * teaching_clarity * forgiveness_focus * 0.08
                self._forgiveness_capacity = min(1.0, self._forgiveness_capacity + forgiveness_increase)

        except Exception as e:
            self.get_logger().warn(f"Failed to process moral teaching: {e}")

    # ── Moral Disgust Memory Dynamics Update ────────────────────────────────
    def _update_moral_disgust_memory(self):
        now = time.time()
        dt = now - self._last_update
        self._last_update = now

        # Contamination history naturally decays over time (memories fade)
        history_decay = self._memory_decay_rate * dt * self._contamination_history
        self._contamination_history = max(0.0, self._contamination_history - history_decay)

        # Sensitivity slowly returns to baseline without reinforcement
        sensitivity_decay = (self._contamination_sensitivity - 0.5) * 0.005 * dt
        self._contamination_sensitivity -= sensitivity_decay
        self._contamination_sensitivity = max(0.3, min(1.0, self._contamination_sensitivity))

        # Purity ideals slowly decay without reinforcement
        ideal_decay = (self._moral_purity_ideal - 0.6) * self._ideal_decay_rate * dt
        self._moral_purity_ideal -= ideal_decay
        self._moral_purity_ideal = max(0.5, min(1.0, self._moral_purity_ideal))

        # Avoidance decreases when not reinforced by threats
        avoidance_decay = self._contamination_avoidance * 0.005 * dt
        self._contamination_avoidance = max(0.3, self._contamination_avoidance - avoidance_decay)

        # Guilt/shame responses slowly decrease without reinforcement
        guilt_decay = self._guilt_response * 0.003 * dt
        shame_decay = self._shame_response * 0.002 * dt
        self._guilt_response = max(0.1, self._guilt_response - guilt_decay)
        self._shame_response = max(0.1, self._shame_response - shame_decay)

        # Restitution drive decreases when not needed
        restitution_decay = max(0.0, (self._contamination_history - self._restitution_threshold)) * 0.01 * dt
        self._restitution_drive = max(0.0, self._restitution_drive - restitution_decay)

        # Forgiveness capacity slowly grows with time (healing)
        forgiveness_growth = self._forgiveness_growth * dt
        self._forgiveness_capacity = min(1.0, self._forgiveness_capacity + forgiveness_growth)

        # Ensure all values stay in valid ranges
        self._contamination_sensitivity = max(0.0, min(1.0, self._contamination_sensitivity))
        self._contamination_history = max(0.0, min(1.0, self._contamination_history))
        self._purification_motivation = max(0.0, min(1.0, self._purification_motivation))
        self._moral_purity_ideal = max(0.0, min(1.0, self._moral_purity_ideal))
        self._contamination_avoidance = max(0.0, min(1.0, self._contamination_avoidance))
        self._guilt_response = max(0.0, min(1.0, self._guilt_response))
        self._shame_response = max(0.0, min(1.0, self._shame_response))
        self._restitution_drive = max(0.0, min(1.0, self._restitution_drive))
        self._forgiveness_capacity = max(0.0, min(1.0, self._forgiveness_capacity))

        # Prepare outputs
        moral_disgust_state = MoralDisgustMemoryState(
            timestamp=now,
            contamination_sensitivity=self._contamination_sensitivity,
            contamination_history=self._contamination_history,
            purification_motivation=self._purification_motivation,
            moral_purity_ideal=self._moral_purity_ideal,
            contamination_avoidance=self._contamination_avoidance,
            guilt_response=self._guilt_response,
            shame_response=self._shame_response,
            restitution_drive=self._restitution_drive,
            forgiveness_capacity=self._forgiveness_capacity
        )
        out = String()
        out.data = to_json(moral_disgust_state)
        self._pub.publish(out)

        # Log significant moral disgust memory dynamics
        if int(now) % 30 == 0:  # Every 30 seconds
            self.get_logger().info(
                f"Moral Disgust Memory - Sens:{self._contamination_sensitivity:.2f} "
                f"Hist:{self._contamination_history:.2f} "
                f"PurMot:{self._purification_motivation:.2f} "
                f"Guilt:{self._guilt_response:.2f} "
                f"Shame:{self._shame_response:.2f}"
            )

def main(args=None):
    rclpy.init(args=args)
    node = MoralDisgustMemoryNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()