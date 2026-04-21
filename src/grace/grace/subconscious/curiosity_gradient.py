"""
grace_agi/subconscious/curiosity_gradient.py
Subconscious Layer — Curiosity Gradient
Information Gap Detection · Novelty Detection · Exploration Drive
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.grace.utils.schemas import CuriosityGradientState, to_json


class CuriosityGradientNode(Node):
    def __init__(self):
        super().__init__("grace_curiosity_gradient")

        # ── Parameters ────────────────────────────────────────────────────────
        self.declare_parameter("update_hz", 0.2)  # Updates every 5 seconds
        self.update_hz = self.get_parameter("update_hz").value

        # ── Internal State ───────────────────────────────────────────────────
        self._information_gap = 0.5            # 0=no gap  1=maximum information gap
        self._curiosity_intensity = 0.6        # 0=no curiosity  1=burning curiosity
        self._novelty_sensitivity = 0.5        # 0=insensitive  1=highly sensitive to novelty
        self._knowledge_confidence = 0.7       # 0=no confidence  1=complete confidence in knowledge
        self._exploration_drive = 0.4          # 0=no drive  1=strong drive to explore
        self._information_novelty = 0.3        # 0=familiar  1=completely novel
        self._learning_progress = 0.5          # 0=no progress  1=rapid learning
        self._boredom_threshold = 0.6          # Threshold below which boredom occurs
        self._last_update = time.time()

        # ── Curiosity Gradient Parameters ───────────────────────────────────
        self._knowledge_decay_rate = 0.01      # Natural decay of knowledge confidence
        self._novelty_decay_rate = 0.02        # How quickly novelty fades
        self._learning_rate = 0.03             # Rate of learning from new information
        self._boredom_rate = 0.015             # Rate at which boredom develops
        self._exploration_decay = 0.01         # Decay of exploration drive when satisfied
        self._gap_curiosity_gain = 0.4         # How much information gap increases curiosity
        self._novelty_curiosity_gain = 0.3     # How much novelty increases curiosity

        # ── Subscribers (Inputs from other systems) ─────────────────────────
        # Novelty detection from perceptual systems
        self.create_subscription(String, "/grace/perception/novelty_signal",
                                 self._on_novelty_signal, 10)
        # Knowledge updates from learning systems
        self.create_subscription(String, "/grace/learning/knowledge_update",
                                 self._on_knowledge_update, 10)
        # Learning progress from educational systems
        self.create_subscription(String, "/grace/learning/progress_report",
                                 self._on_learning_progress, 10)
        # Boredom signals from engagement monitoring
        self.create_subscription(String, "/grace/engagement/boredom_signal",
                                 self._on_boredom_signal, 10)
        # Satisfaction from completed exploration
        self.create_subscription(String, "/grace/exploration/satisfaction_signal",
                                 self._on_satisfaction_signal, 10)

        # ── Publishers (Outputs to other systems) ───────────────────────────
        self._pub = self.create_publisher(String, "/grace/subconscious/curiosity_gradient_state", 10)
        self.create_timer(1.0 / self.update_hz, self._update_curiosity_gradient)
        self.get_logger().info("Curiosity Gradient ready.")

    # ── Input Processing ─────────────────────────────────────────────────────
    def _on_novelty_signal(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Novelty signal increases information gap and curiosity
            novelty_level = data.get("novelty_level", 0.0)  # 0=familiar  1=novel
            novelty_confidence = data.get("confidence", 0.5)  # Confidence in novelty detection

            # Update information novelty
            self._information_novelty = novelty_level * novelty_confidence

            # Novelty increases information gap
            gap_increase = novelty_level * self._novelty_sensitivity * 0.3
            self._information_gap = min(1.0, self._information_gap + gap_increase)

            # Novelty increases curiosity intensity
            curiosity_increase = novelty_level * self._novelty_curiosity_gain
            self._curiosity_intensity = min(1.0, self._curiosity_intensity + curiosity_increase)

            # High novelty increases exploration drive
            if novelty_level > 0.5:
                exploration_boost = (novelty_level - 0.5) * 0.4
                self._exploration_drive = min(1.0, self._exploration_drive + exploration_boost)

        except Exception as e:
            self.get_logger().warn(f"Failed to process novelty signal: {e}")

    def _on_knowledge_update(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Knowledge updates affect knowledge confidence and information gap
            new_knowledge = data.get("knowledge_amount", 0.0)  # Amount of new knowledge acquired
            knowledge_quality = data.get("quality", 0.5)       # Quality of the knowledge
            knowledge_relevance = data.get("relevance", 0.5)   # Relevance to current interests

            # Knowledge increases confidence
            confidence_gain = new_knowledge * knowledge_quality * knowledge_relevance * 0.2
            self._knowledge_confidence = min(1.0, self._knowledge_confidence + confidence_gain)

            # Knowledge reduces information gap (we know more now)
            gap_reduction = new_knowledge * knowledge_relevance * 0.3
            self._information_gap = max(0.0, self._information_gap - gap_reduction)

            # High-quality relevant knowledge increases learning progress
            if knowledge_quality > 0.6 and knowledge_relevance > 0.6:
                learning_boost = new_knowledge * knowledge_quality * knowledge_relevance * 0.1
                self._learning_progress = min(1.0, self._learning_progress + learning_boost)

        except Exception as e:
            self.get_logger().warn(f"Failed to process knowledge update: {e}")

    def _on_learning_progress(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Direct learning progress updates
            progress_rate = data.get("progress_rate", 0.0)  # Rate of learning
            efficiency = data.get("efficiency", 0.5)       # Learning efficiency
            difficulty = data.get("difficulty", 0.5)       # Perceived difficulty

            # Update learning progress
            self._learning_progress = progress_rate

            # High efficiency and moderate difficulty boost curiosity
            if efficiency > 0.5 and 0.3 < difficulty < 0.7:
                curiosity_boost = efficiency * 0.2
                self._curiosity_intensity = min(1.0, self._curiosity_intensity + curiosity_boost)

            # Successful learning increases knowledge confidence
            if progress_rate > 0.3:
                confidence_boost = progress_rate * 0.1
                self._knowledge_confidence = min(1.0, self._knowledge_confidence + confidence_boost)

        except Exception as e:
            self.get_logger().warn(f"Failed to process learning progress: {e}")

    def _on_boredom_signal(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Boredom signals decrease curiosity and increase boredom threshold
            boredom_level = data.get("boredom_level", 0.0)  # 0=engaged  1=bored
            boredom_confidence = data.get("confidence", 0.5)  # Confidence in boredom detection

            # Update boredom threshold based on boredom experience
            threshold_adjustment = boredom_level * boredom_confidence * 0.1
            self._boredom_threshold += threshold_adjustment
            self._boredom_threshold = max(0.1, min(0.9, self._boredom_threshold))

            # High boredom decreases curiosity intensity
            if boredom_level > self._boredom_threshold:
                curiosity_reduction = (boredom_level - self._boredom_threshold) * 0.3
                self._curiosity_intensity = max(0.0, self._curiosity_intensity - curiosity_reduction)

            # Boredom decreases exploration drive
            exploration_reduction = boredom_level * 0.2
            self._exploration_drive = max(0.0, self._exploration_drive - exploration_reduction)

        except Exception as e:
            self.get_logger().warn(f"Failed to process boredom signal: {e}")

    def _on_satisfaction_signal(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Satisfaction from exploration reduces exploration drive and information gap
            satisfaction_level = data.get("satisfaction_level", 0.0)  # 0=unsatisfied  1=satisfied
            exploration_complete = data.get("exploration_complete", False)  # Whether exploration is complete

            # Satisfaction reduces exploration drive
            drive_reduction = satisfaction_level * self._exploration_decay
            self._exploration_drive = max(0.0, self._exploration_drive - drive_reduction)

            # Completed exploration significantly reduces information gap
            if exploration_complete:
                gap_reduction = satisfaction_level * 0.5
                self._information_gap = max(0.0, self._information_gap - gap_reduction)

            # Satisfaction moderately increases knowledge confidence
            confidence_boost = satisfaction_level * 0.1
            self._knowledge_confidence = min(1.0, self._knowledge_confidence + confidence_boost)

            # Satisfaction can lead to boredom if overdone
            if satisfaction_level > 0.8:
                boredom_increase = (satisfaction_level - 0.8) * 0.2
                self._boredom_threshold = min(0.9, self._boredom_threshold + boredom_increase)

        except Exception as e:
            self.get_logger().warn(f"Failed to process satisfaction signal: {e}")

    # ── Curiosity Gradient Dynamics Update ───────────────────────────────────
    def _update_curiosity_gradient(self):
        now = time.time()
        dt = now - self._last_update
        self._last_update = now

        # Knowledge naturally decays over time (use it or lose it)
        knowledge_decay = self._knowledge_decay_rate * dt * self._knowledge_confidence
        self._knowledge_confidence = max(0.1, self._knowledge_confidence - knowledge_decay)

        # Novelty naturally decays (familiarity increases)
        novelty_decay = self._novelty_decay_rate * dt * self._information_novelty
        self._information_novelty = max(0.0, self._information_novelty - novelty_decay)

        # Boredom naturally develops over time with low stimulation
        boredom_development = self._boredom_rate * dt * (1.0 - self._information_novelty)
        self._boredom_threshold = min(0.8, self._boredom_threshold + boredom_development)

        # Exploration drive decays when not stimulated
        exploration_decay = self._exploration_decay * dt * (1.0 - self._information_gap)
        self._exploration_drive = max(0.0, self._exploration_drive - exploration_decay)

        # Information gap increases with lack of knowledge and high novelty seeking
        knowledge_lack = 1.0 - self._knowledge_confidence
        novelty_seeking = self._novelty_sensitivity
        gap_increase = knowledge_lack * novelty_seeking * 0.1 * dt
        self._information_gap = min(1.0, self._information_gap + gap_increase)

        # Curiosity intensity driven by information gap and novelty
        gap_driven_curiosity = self._information_gap * self._gap_curiosity_gain
        novelty_driven_curiosity = self._information_novelty * self._novelty_curiosity_gain
        base_curiosity = gap_driven_curiosity + novelty_driven_curiosity

        # Apply boredom suppression
        boredom_factor = 1.0 - min(1.0, (self._boredom_threshold - 0.3) * 2.0)  # 0 when boredom high
        self._curiosity_intensity = base_curiosity * boredom_factor
        self._curiosity_intensity = max(0.0, min(1.0, self._curiosity_intensity))

        # Novelty sensitivity increases with exploratory drive and decreases with knowledge
        sensitivity_boost = self._exploration_drive * 0.1
        sensitivity_reduction = self._knowledge_confidence * 0.05
        self._novelty_sensitivity += (sensitivity_boost - sensitivity_reduction) * dt
        self._novelty_sensitivity = max(0.1, min(1.0, self._novelty_sensitivity))

        # Prepare outputs
        curiosity_state = CuriosityGradientState(
            timestamp=now,
            information_gap=self._information_gap,
            curiosity_intensity=self._curiosity_intensity,
            novelty_sensitivity=self._novelty_sensitivity,
            knowledge_confidence=self._knowledge_confidence,
            exploration_drive=self._exploration_drive,
            information_novelty=self._information_novelty,
            learning_progress=self._learning_progress,
            boredom_threshold=self._boredom_threshold
        )
        out = String()
        out.data = to_json(curiosity_state)
        self._pub.publish(out)

        # Log significant curiosity gradient dynamics
        if int(now) % 20 == 0:  # Every 20 seconds
            self.get_logger().info(
                f"Curiosity Gradient - Gap:{self._information_gap:.2f} "
                f"Intensity:{self._curiosity_intensity:.2f} "
                f"Novelty:{self._information_novelty:.2f} "
                f"Confidence:{self._knowledge_confidence:.2f} "
                f"Explore:{self._exploration_drive:.2f}"
            )

    def main(args=None):
        rclpy.init(args=args)
        node = CuriosityGradientNode()
        rclpy.spin(node)
        node.destroy_node()
        rclpy.shutdown()