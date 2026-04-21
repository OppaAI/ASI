"""
grace_agi/subconscious/aesthetic_sensitivity.py
Subconscious Layer — Aesthetic Sensitivity System
Beauty · Harmony · Sublime · Aesthetic Judgment
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.grace.utils.schemas import AestheticSensitivityState, to_json


class AestheticSensitivityNode(Node):
    def __init__(self):
        super().__init__("grace_aesthetic_sensitivity")

        # ── Parameters ────────────────────────────────────────────────────────
        self.declare_parameter("update_hz", 0.1)  # Updates every 10 seconds
        self.update_hz = self.get_parameter("update_hz").value

        # ── Internal State ───────────────────────────────────────────────────
        self._beauty_sensitivity = 0.6          # 0=insensitive  1=highly sensitive to beauty
        self._harmony_appreciation = 0.5        # 0=no appreciation  1=deep appreciation of harmony
        self._sublime_responsiveness = 0.3      # 0=unresponsive  1=highly responsive to sublime
        self._aesthetic_judgment_confidence = 0.4 # 0=no confidence  1=high confidence in aesthetic judgments
        self._novelty_seeking = 0.5             # 0=traditional  1=seeks novel aesthetic experiences
        self._emotional_resonance = 0.5         # 0=no resonance  1=deep emotional resonance with art
        self._cultural_openness = 0.5           # 0=ethnocentric  1=open to diverse aesthetic traditions
        self._aesthetic_memory = 0.4            # 0=poor recall  1=rich aesthetic memory
        self._creative_inspiration = 0.5        # 0=inspired  1=highly inspired by aesthetic experiences
        self._last_update = time.time()

        # ── Aesthetic Sensitivity Parameters ───────────────────────────────
        self._sensitivity_decay = 0.005         # Natural decay of sensitivity
        self._appreciation_growth = 0.008       # How appreciation grows with exposure
        self._judgment_confidence_growth = 0.01 # How confidence grows with experience
        self._novelty_satisfaction = 0.006      # How novelty seeking satisfaction affects it
        self._resonance_decay = 0.004           # How emotional resonance fades
        self._cultural_openness_growth = 0.005  # How openness grows with exposure
        self._memory_retention = 0.007          # How well aesthetic memories are retained
        self._inspiration_decay = 0.003         # How creative inspiration fades
        self._inspiration_growth = 0.012        # How inspiration grows with aesthetic experiences

        # ── Subscribers (Inputs from other systems) ─────────────────────────
        # Aesthetic experiences from perception systems
        self.create_subscription(String, "/grace/perception/aesthetic_experience",
                                 self._on_aesthetic_experience, 10)
        # Artistic creations from expressive systems
        self.create_subscription(String, "/grace/expression/artistic_creation",
                                 self._on_artistic_creation, 10)
        # Cultural exposure from social systems
        self.create_subscription(String, "/grace/social/cultural_exposure",
                                 self._on_cultural_exposure, 10)
        # Aesthetic judgments from conscious evaluation
        self.create_subscription(String, "/grace/conscious/aesthetic_judgment",
                                 self._on_aesthetic_judgment, 10)
        # Emotional responses to aesthetic stimuli
        self.create_subscription(String, "/grace/emotion/aesthetic_response",
                                 self._on_aesthetic_response, 10)
        # Creative inspirations from imagination systems
        self.create_subscription(String, "/grace/imagination/creative_inspiration",
                                 self._on_creative_inspiration, 10)
        # Cultural feedback from social systems
        self.create_subscription(String, "/grace/social/cultural_feedback",
                                 self._on_cultural_feedback, 10)

        # ── Publishers (Outputs to other systems) ───────────────────────────
        self._pub = self.create_publisher(String, "/grace/subconscious/aesthetic_sensitivity_state", 10)
        self.create_timer(1.0 / self.update_hz, self._update_aesthetic_sensitivity)
        self.get_logger().info("Aesthetic Sensitivity System ready.")

    # ── Input Processing ─────────────────────────────────────────────────────
    def _on_aesthetic_experience(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Aesthetic experiences affect sensitivity, appreciation, and memory
            beauty_level = data.get("beauty_level", 0.0)      # 0=not beautiful  1=beautiful
            harmony_level = data.get("harmony_level", 0.0)    # 0=not harmonious  1=harmonious
            sublime_level = data.get("sublime_level", 0.0)    # 0=not sublime  1=sublime
            novelty_level = data.get("novelty_level", 0.0)    # 0=familiar  1=novel
            emotional_impact = data.get("emotional_impact", 0.0) # Emotional impact of experience
            cultural_significance = data.get("cultural_significance", 0.0) # Cultural significance

            # Beauty experiences increase beauty sensitivity
            if beauty_level > 0.5:
                sensitivity_increase = (beauty_level - 0.5) * self._appreciation_growth
                self._beauty_sensitivity = min(1.0, self._beauty_sensitivity + sensitivity_increase)

            # Harmony experiences increase harmony appreciation
            if harmony_level > 0.5:
                appreciation_increase = (harmony_level - 0.5) * self._appreciation_growth
                self._harmony_appreciation = min(1.0, self._harmony_appreciation + appreciation_increase)

            # Sublime experiences increase sublime responsiveness
            if sublime_level > 0.5:
                responsiveness_increase = (sublime_level - 0.5) * self._appreciation_growth * 1.5
                self._sublime_responsiveness = min(1.0, self._sublime_responsiveness + responsiveness_increase)

            # Novelty experiences affect novelty seeking
            novelty_satisfaction = novelty_level * 0.5  # Familiar things satisfy less
            novelty_change = (novelty_satisfaction - 0.5) * self._novelty_satisfaction
            self._novelty_seeking += novelty_change
            self._novelty_seeking = max(0.0, min(1.0, self._novelty_seeking))

            # Emotional impact increases emotional resonance
            resonance_increase = emotional_impact * self._appreciation_growth
            self._emotional_resonance = min(1.0, self._emotional_resonance + resonance_increase)

            # Cultural significance increases cultural openness
            if cultural_significance > 0.3:
                openness_increase = (cultural_significance - 0.3) * self._cultural_openness_growth
                self._cultural_openness = min(1.0, self._cultural_openness + openness_increase)

            # Significant experiences improve aesthetic memory
            significance = (beauty_level + harmony_level + sublime_level) / 3.0
            if significance > 0.4:
                memory_increase = significance * self._memory_retention
                self._aesthetic_memory = min(1.0, self._aesthetic_memory + memory_increase)

            # Inspiring experiences increase creative inspiration
            inspiration_level = data.get("inspiration_level", 0.0)
            if inspiration_level > 0.4:
                inspiration_increase = (inspiration_level - 0.4) * self._inspiration_growth
                self._creative_inspiration = min(1.0, self._creative_inspiration + inspiration_increase)

        except Exception as e:
            self.get_logger().warn(f"Failed to process aesthetic experience: {e}")

    def _on_artistic_creation(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Creating art affects confidence, emotional resonance, and inspiration
            creation_quality = data.get("quality", 0.0)       # 0=poor  1=excellent
            creation_novelty = data.get("novelty", 0.0)       # 0=derivative  1=novel
            creation_emotional = data.get("emotional_content", 0.0) # Emotional content
            creation_cultural = data.get("cultural_elements", 0.0) # Cultural elements used

            # Successful creation increases judgment confidence
            if creation_quality > 0.5:
                confidence_increase = (creation_quality - 0.5) * self._judgment_confidence_growth
                self._aesthetic_judgment_confidence = min(1.0, self._aesthetic_judgment_confidence + confidence_increase)

            # Novel creations increase novelty seeking satisfaction
            if creation_novelty > 0.5:
                novelty_satisfaction = (creation_novelty - 0.5) * 0.3
                self._novelty_seeking = max(0.0, min(1.0, self._novelty_seeking + novelty_satisfaction))

            # Emotional content increases emotional resonance
            if creation_emotional > 0.4:
                resonance_increase = (creation_emotional - 0.4) * self._appreciation_growth * 0.8
                self._emotional_resonance = min(1.0, self._emotional_resonance + resonance_increase)

            # Cultural elements increase cultural openness
            if creation_cultural > 0.3:
                openness_increase = (creation_cultural - 0.3) * self._cultural_openness_growth
                self._cultural_openness = min(1.0, self._cultural_openness + openness_increase)

            # Creative acts inspire further creativity
            inspiration_increase = creation_quality * self._inspiration_growth * 0.5
            self._creative_inspiration = min(1.0, self._creative_inspiration + inspiration_increase)

            # Creating beauty increases beauty sensitivity
            beauty_content = data.get("beauty_content", 0.0)
            if beauty_content > 0.5:
                sensitivity_increase = (beauty_content - 0.5) * self._appreciation_growth
                self._beauty_sensitivity = min(1.0, self._beauty_sensitivity + sensitivity_increase)

        except Exception as e:
            self.get_logger().warn(f"Failed to process artistic creation: {e}")

    def _on_cultural_exposure(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Cultural exposure affects openness and appreciation
            cultural_value = data.get("value", 0.0)           # 0=no value  1=high value
            cultural_novelty = data.get("novelty", 0.0)       # 0=familiar  1=novel to culture
            cultural_complexity = data.get("complexity", 0.0) # 0=simple  1=complex
            cultural_authenticity = data.get("authenticity", 0.0) # 0=inauthentic  1=authentic

            # Exposure to valuable culture increases openness
            if cultural_value > 0.4:
                openness_increase = (cultural_value - 0.4) * self._cultural_openness_growth * 0.5
                self._cultural_openness = min(1.0, self._cultural_openness + openness_increase)

            # Novel cultural experiences increase novelty seeking
            if cultural_novelty > 0.5:
                novelty_satisfaction = (cultural_novelty - 0.5) * self._novelty_satisfaction * 0.4
                self._novelty_seeking += novelty_satisfaction
                self._novelty_seeking = max(0.0, min(1.0, self._novelty_seeking))

            # Complex cultural experiences increase appreciation
            if cultural_complexity > 0.4:
                appreciation_increase = (cultural_complexity - 0.4) * self._appreciation_growth * 0.3
                self._harmony_appreciation = min(1.0, self._harmony_appreciation + appreciation_increase)
                self._beauty_sensitivity = min(1.0, self._beauty_sensitivity + appreciation_increase * 0.5)

            # Authentic cultural experiences increase emotional resonance
            if cultural_authenticity > 0.5:
                resonance_increase = (cultural_authenticity - 0.5) * self._appreciation_growth
                self._emotional_resonance = min(1.0, self._emotional_resonance + resonance_increase)

            # Cultural experiences improve aesthetic memory
            memory_value = (cultural_value + cultural_novelty) / 2.0
            if memory_value > 0.3:
                memory_increase = memory_value * self._memory_retention
                self._aesthetic_memory = min(1.0, self._aesthetic_memory + memory_increase)

        except Exception as e:
            self.get_logger().warn(f"Failed to process cultural exposure: {e}")

    def _on_aesthetic_judgment(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Aesthetic judgments affect confidence and memory
            judgment_confidence = data.get("confidence", 0.0) # 0=no confidence  1=full confidence
            judgment_accuracy = data.get("accuracy", 0.5)     # How accurate the judgment was
            judgment_consensus = data.get("consensus", 0.5)   # How much others agreed
            judgment_novelty = data.get("novelty_recognized", 0.0) # Novelty recognized in judgment

            # Successful judgments increase confidence
            if judgment_accuracy > 0.5:
                confidence_increase = (judgment_accuracy - 0.5) * self._judgment_confidence_growth
                self._aesthetic_judgment_confidence = min(1.0, self._aesthetic_judgment_confidence + confidence_increase)

            # Consensus confirms judgment validity
            consensus_bonus = judgment_consensus * 0.2
            if judgment_accuracy > 0.4:
                confidence_increase = consensus_bonus * self._judgment_confidence_growth
                self._aesthetic_judgment_confidence = min(1.0, self._aesthetic_judgment_confidence + confidence_increase)

            # Recognizing novelty increases novelty seeking
            if judgment_novelty > 0.4:
                novelty_increase = (judgment_novelty - 0.4) * self._novelty_satisfaction
                self._novelty_seeking = max(0.0, min(1.0, self._novelty_seeking + novelty_increase))

            # Judgments about beauty/harmony/sublime increase respective sensitivities
            beauty_judgment = data.get("beauty_judgment", 0.0)
            harmony_judgment = data.get("harmony_judgment", 0.0)
            sublime_judgment = data.get("sublime_judgment", 0.0)

            if beauty_judgment > 0.5:
                sensitivity_increase = (beauty_judgment - 0.5) * self._appreciation_growth * 0.3
                self._beauty_sensitivity = min(1.0, self._beauty_sensitivity + sensitivity_increase)

            if harmony_judgment > 0.5:
                appreciation_increase = (harmony_judgment - 0.5) * self._appreciation_growth * 0.3
                self._harmony_appreciation = min(1.0, self._harmony_appreciation + appreciation_increase)

            if sublime_judgment > 0.5:
                responsiveness_increase = (sublime_judgment - 0.5) * self._appreciation_growth * 0.5
                self._sublime_responsiveness = min(1.0, self._sublime_responsiveness + responsiveness_increase)

        except Exception as e:
            self.get_logger().warn(f"Failed to process aesthetic judgment: {e}")

    def _on_aesthetic_response(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Emotional responses to aesthetics affect resonance and memory
            emotional_intensity = data.get("intensity", 0.0)  # 0=no emotion  1=intense emotion
            emotional_valence = data.get("valence", 0.5)      # 0=negative  1=positive
            aesthetic_type = data.get("type", "general")      # beauty, harmony, sublime, etc.
            memory_worthiness = data.get("memory_worthiness", 0.5) # Worth remembering

            # Positive emotional responses increase emotional resonance
            if emotional_valence > 0.5:
                resonance_increase = (emotional_valence - 0.5) * emotional_intensity * self._appreciation_growth
                self._emotional_resonance = min(1.0, self._emotional_resonance + resonance_increase)
            else:
                # Negative emotions still create strong memories but may decrease liking
                resonance_increase = abs(emotional_valence - 0.5) * emotional_intensity * self._appreciation_growth * 0.3
                self._emotional_resonance = min(1.0, self._emotional_resonance + resonance_increase)

            # Memorable experiences improve aesthetic memory
            if memory_worthiness > 0.5:
                memory_increase = memory_worthiness * self._memory_retention * 0.5
                self._aesthetic_memory = min(1.0, self._aesthetic_memory + memory_increase)

            # Strong emotional responses increase inspiration
            if emotional_intensity > 0.6:
                inspiration_increase = emotional_intensity * self._inspiration_growth * 0.4
                self._creative_inspiration = min(1.0, self._creative_inspiration + inspiration_increase)

            # Responses to specific aesthetic types increase respective sensitivities
            if aesthetic_type == "beauty":
                sensitivity_increase = emotional_intensity * self._appreciation_growth * 0.2
                self._beauty_sensitivity = min(1.0, self._beauty_sensitivity + sensitivity_increase)
            elif aesthetic_type == "harmony":
                appreciation_increase = emotional_intensity * self._appreciation_growth * 0.2
                self._harmony_appreciation = min(1.0, self._harmony_appreciation + appreciation_increase)
            elif aesthetic_type == "sublime":
                responsiveness_increase = emotional_intensity * self._appreciation_growth * 0.3
                self._sublime_responsiveness = min(1.0, self._sublime_responsiveness + responsiveness_increase)

        except Exception as e:
            self.get_logger().warn(f"Failed to process aesthetic response: {e}")

    def _on_creative_inspiration(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Creative inspirations affect inspiration levels and novelty seeking
            inspiration_level = data.get("level", 0.0)        # 0=no inspiration  1=high inspiration
            inspiration_novelty = data.get("novelty", 0.0)    # 0=familiar  1=novel inspiration
            inspiration_purity = data.get("purity", 0.5)      # 0=derivative  1=pure inspiration

            # Inspiration increases creative inspiration (obviously)
            inspiration_increase = inspiration_level * self._inspiration_growth
            self._creative_inspiration = min(1.0, self._creative_inspiration + inspiration_increase)

            # Novel inspiration increases novelty seeking
            if inspiration_novelty > 0.5:
                novelty_satisfaction = (inspiration_novelty - 0.5) * self._novelty_satisfaction
                self._novelty_seeking += novelty_satisfaction
                self._novelty_seeking = max(0.0, min(1.0, self._novelty_seeking))

            # Pure inspiration increases aesthetic judgment confidence
            if inspiration_purity > 0.6:
                confidence_increase = (inspiration_purity - 0.6) * self._judgment_confidence_growth
                self._aesthetic_judgment_confidence = min(1.0, self._aesthetic_judgment_confidence + confidence_increase)

            # Inspiration often involves beauty/harmony/sublime elements
            beauty_content = data.get("beauty_content", 0.0)
            harmony_content = data.get("harmony_content", 0.0)
            sublime_content = data.get("sublime_content", 0.0)

            if beauty_content > 0.4:
                sensitivity_increase = (beauty_content - 0.4) * self._appreciation_growth * 0.3
                self._beauty_sensitivity = min(1.0, self._beauty_sensitivity + sensitivity_increase)

            if harmony_content > 0.4:
                appreciation_increase = (harmony_content - 0.4) * self._appreciation_growth * 0.3
                self._harmony_appreciation = min(1.0, self._harmony_appreciation + appreciation_increase)

            if sublime_content > 0.4:
                responsiveness_increase = (sublime_content - 0.4) * self._appreciation_growth * 0.4
                self._sublime_responsiveness = min(1.0, self._sublime_responsiveness + responsiveness_increase)

        except Exception as e:
            self.get_logger().warn(f"Failed to process creative inspiration: {e}")

    def _on_cultural_feedback(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Cultural feedback affects cultural openness and memory
            feedback_positivity = data.get("positivity", 0.5) # 0=negative  1=positive feedback
            feedback_relevance = data.get("relevance", 0.5)   # How relevant to cultural engagement
            feedback_authenticity = data.get("authenticity", 0.5) # Authenticity of feedback

            # Positive feedback increases cultural openness
            if feedback_positivity > 0.5:
                openness_increase = (feedback_positivity - 0.5) * self._cultural_openness_growth * 0.3
                self._cultural_openness = min(1.0, self._cultural_openness + openness_increase)

            # Relevant, authentic feedback increases cultural memory
            memory_value = feedback_relevance * feedback_authenticity
            if memory_value > 0.4:
                memory_increase = memory_value * self._memory_retention
                self._aesthetic_memory = min(1.0, self._aesthetic_memory + memory_increase)

            # Negative feedback from authentic sources can increase openness (challenge response)
            if feedback_positivity < 0.3 and feedback_authenticity > 0.6:
                challenge_increase = (0.3 - feedback_positivity) * feedback_authenticity * 0.2
                self._cultural_openness = min(1.0, self._cultural_openness + challenge_increase)

        except Exception as e:
            self.get_logger().warn(f"Failed to process cultural feedback: {e}")

    # ── Aesthetic Sensitivity System Dynamics Update ────────────────────────
    def _update_aesthetic_sensitivity(self):
        now = time.time()
        dt = now - self._last_update
        self._last_update = now

        # Sensitivities naturally decay over time without stimulation
        beauty_decay = self._beauty_sensitivity * self._sensitivity_decay * dt
        harmony_decay = self._harmony_appreciation * self._sensitivity_decay * dt
        sublime_decay = self._sublime_responsiveness * self._sensitivity_decay * dt
        resonance_decay = self._emotional_resonance * self._resonance_decay * dt
        memory_decay = self._aesthetic_memory * self._memory_retention * dt
        inspiration_decay = self._creative_inspiration * self._inspiration_decay * dt

        self._beauty_sensitivity = max(0.2, self._beauty_sensitivity - beauty_decay)
        self._harmony_appreciation = max(0.2, self._harmony_appreciation - harmony_decay)
        self._sublime_responsiveness = max(0.1, self._sublime_responsiveness - sublime_decay)
        self._emotional_resonance = max(0.2, self._emotional_resonance - resonance_decay)
        self._aesthetic_memory = max(0.2, self._aesthetic_memory - memory_decay)
        self._creative_inspiration = max(0.2, self._creative_inspiration - inspiration_decay)

        # Judgment confidence slowly grows with time and experience
        confidence_growth = self._judgment_confidence_growth * dt * (1.0 - self._aesthetic_judgment_confidence)
        self._aesthetic_judgment_confidence = min(1.0, self._aesthetic_judgment_confidence + confidence_growth)

        # Novelty seeking seeks equilibrium based on experiences
        novelty_equilibrium = 0.5  # Balance between novelty and familiarity
        novelty_drive = (novelty_equilibrium - self._novelty_seeking) * self._novelty_satisfaction * dt
        self._novelty_seeking += novelty_drive
        self._novelty_seeking = max(0.0, min(1.0, self._novelty_seeking))

        # Cultural openness grows slowly with exposure
        openness_growth = self._cultural_openness_growth * dt * (1.0 - self._cultural_openness)
        self._cultural_openness = min(1.0, self._cultural_openness + openness_growth)

        # Ensure all values stay in valid ranges
        self._beauty_sensitivity = max(0.0, min(1.0, self._beauty_sensitivity))
        self._harmony_appreciation = max(0.0, min(1.0, self._harmony_appreciation))
        self._sublime_responsiveness = max(0.0, min(1.0, self._sublime_responsiveness))
        self._aesthetic_judgment_confidence = max(0.0, min(1.0, self._aesthetic_judgment_confidence))
        self._novelty_seeking = max(0.0, min(1.0, self._novelty_seeking))
        self._emotional_resonance = max(0.0, min(1.0, self._emotional_resonance))
        self._cultural_openness = max(0.0, min(1.0, self._cultural_openness))
        self._aesthetic_memory = max(0.0, min(1.0, self._aesthetic_memory))
        self._creative_inspiration = max(0.0, min(1.0, self._creative_inspiration))

        # Prepare outputs
        aesthetic_state = AestheticSensitivityState(
            timestamp=now,
            beauty_sensitivity=self._beauty_sensitivity,
            harmony_appreciation=self._harmony_appreciation,
            sublime_responsiveness=self._sublime_responsiveness,
            aesthetic_judgment_confidence=self._aesthetic_judgment_confidence,
            novelty_seeking=self._novelty_seeking,
            emotional_resonance=self._emotional_resonance,
            cultural_openness=self._cultural_openness,
            aesthetic_memory=self._aesthetic_memory,
            creative_inspiration=self._creative_inspiration
        )
        out = String()
        out.data = to_json(aesthetic_state)
        self._pub.publish(out)

        # Log significant aesthetic sensitivity dynamics
        if int(now) % 30 == 0:  # Every 30 seconds
            self.get_logger().info(
                f"Aesthetic Sensitivity - Beauty:{self._beauty_sensitivity:.2f} "
                f"Harmony:{self._harmony_appreciation:.2f} "
                f"Sublime:{self._sublime_responsiveness:.2f} "
                f"Judgment:{self._aesthetic_judgment_confidence:.2f} "
                f"Novelty:{self._novelty_seeking:.2f}"
            )

def main(args=None):
    rclpy.init(args=args)
    node = AestheticSensitivityNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()