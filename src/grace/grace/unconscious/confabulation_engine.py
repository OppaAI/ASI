"""
grace_agi/unconscious/confabulation_engine.py
Unconscious Layer — Confabulation Engine
Post-Hoc Narrative Generation
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.grace.utils.schemas import ConfabulationState, to_json


class ConfabulationEngineNode(Node):
    def __init__(self):
        super().__init__("grace_confabulation_engine")

        # ── Parameters ────────────────────────────────────────────────────────
        self.declare_parameter("update_hz", 0.5)  # Updates every 2 seconds
        self.update_hz = self.get_parameter("update_hz").value

        # ── Internal State ───────────────────────────────────────────────────
        self._recent_narrative = ""          # Most recent generated narrative
        self._narrative_confidence = 0.5     # Confidence in current narrative (0-1)
        self._gap_detected = False           # Whether a narrative gap was detected
        self._gap_severity = 0.0             # How severe the gap is (0-1)
        self._last_update = time.time()
        self._confabulation_threshold = 0.4  # Gap severity needed to trigger confabulation

        # ── Confabulation Tendencies ─────────────────────────────────────────
        self._self_serving_bias = 0.6        # Tendency to make self look good
        self._coherence_bias = 0.7           # Tendency to prefer coherent stories
        self._familiarity_bias = 0.5         # Tendency to use familiar elements
        self._optimism_bias = 0.4            # Tendency toward positive outcomes
        self._last_confabulation_time = 0.0  # When last confabulation occurred
        self._confabulation_cooldown = 5.0   # Seconds between confabulations

        # ── Subscribers (Inputs from other systems) ─────────────────────────
        # Memory access/failure signals
        self.create_subscription(String, "/grace/subconscious/memory_access",
                                 self._on_memory_access, 10)
        # Prediction errors indicating model mismatch
        self.create_subscription(String, "/grace/unconscious/prediction_error",
                                 self._on_prediction_error, 10)
        # Sense of agency violations
        self.create_subscription(String, "/grace/hidden/error_monitoring",
                                 self._on_agency_violation, 10)
        # Incoherent global workspace broadcasts
        self.create_subscription(String, "/grace/conscious/global_workspace",
                                 self._on_incoherent_broadcast, 10)
        # Metacognitive uncertainty signals
        self.create_subscription(String, "/grace/conscious/metacognition",
                                 self._on_metacognitive_uncertainty, 10)

        # ── Publishers (Outputs to other systems) ───────────────────────────
        self._pub = self.create_publisher(String, "/grace/unconscious/confabulation_state", 10)
        self.create_timer(1.0 / self.update_hz, self._update_confabulation)
        self.get_logger().info("Confabulation Engine ready.")

    # ── Input Processing (Gap Detection) ────────────────────────────────────
    def _on_memory_access(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Memory access failures or low confidence trigger confabulation
            access_success = data.get("success", True)  # True=success False=failure
            confidence = data.get("confidence", 0.8)    # 0-1 confidence in memory
            memory_importance = data.get("importance", 0.5)  # How important was the memory

            if not access_success or confidence < 0.6:
                # Memory gap detected
                gap_severity = (1.0 - float(access_success)) * 0.5 + (1.0 - confidence) * 0.5
                gap_severity *= memory_importance  # Important gaps matter more
                self._detect_narrative_gap(gap_severity, "memory_access")
        except Exception as e:
            self.get_logger().warn(f"Failed to process memory access: {e}")

    def _on_prediction_error(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Large prediction errors indicate model-reality mismatch
            error_magnitude = data.get("error_magnitude", 0.0)  # 0-1
            precision_weight = data.get("precision_weight", 1.0)
            weighted_error = error_magnitude * precision_weight
            source = data.get("source", "unknown")

            if weighted_error > 0.3:  # Significant prediction error
                # Prediction errors create narrative gaps needing explanation
                gap_severity = min(1.0, weighted_error * 0.8)
                self._detect_narrative_gap(gap_severity, f"prediction_error_{source}")
        except Exception as e:
            self.get_logger().warn(f"Failed to process prediction error: {e}")

    def _on_agency_violation(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Sense of agency violations (I didn't do that!) trigger confabulation
            violation_significance = data.get("significance", 0.0)  # 0-1
            if violation_significance > 0.4:
                gap_severity = violation_significance * 0.6
                self._detect_narrative_gap(gap_severity, "agency_violation")
        except Exception as e:
            self.get_logger().warn(f"Failed to process agency violation: {e}")

    def _on_incoherent_broadcast(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Incoherent or low-salience broadcasts create explanatory gaps
            salience = data.get("salience", 0.5)  # 0-1 salience of broadcast
            if salience < 0.3:  # Low salience suggests poor integration
                gap_severity = (1.0 - salience) * 0.7
                self._detect_narrative_gap(gap_severity, "incoherent_broadcast")
        except Exception as e:
            self.get_logger().warn(f"Failed to process incoherent broadcast: {e}")

    def _on_metacognitive_uncertainty(self, msg: String):
        try:
            data = json.loads(msg.data)
            # High metacognitive uncertainty increases confabulation tendency
            uncertainty = data.get("epistemic_flags", [])  # List of uncertainty flags
            uncertainty_score = len([f for f in uncertainty if f in ["uncertain", "speculative", "guess"]]) / max(len(uncertainty), 1)
            if uncertainty_score > 0.5:
                gap_severity = uncertainty_score * 0.4
                self._detect_narrative_gap(gap_severity, "metacognitive_uncertainty")
        except Exception as e:
            self.get_logger().warn(f"Failed to process metacognitive uncertainty: {e}")

    def _detect_narrative_gap(self, severity: float, source: str):
        """Detect a narrative gap that may trigger confabulation"""
        self._gap_detected = True
        self._gap_severity = max(self._gap_severity, severity)
        # Track recent gap sources (for debugging/monitoring)
        if not hasattr(self, '_recent_gap_sources'):
            self._recent_gap_sources = []
        self._recent_gap_sources.append({
            'source': source,
            'severity': severity,
            'timestamp': time.time()
        })
        # Keep only recent sources
        cutoff = time.time() - 30.0  # Last 30 seconds
        self._recent_gap_sources = [s for s in self._recent_gap_sources if s['timestamp'] > cutoff]

    # ── Confabulation Dynamics Update ───────────────────────────────────────
    def _update_confabulation(self):
        now = time.time()
        dt = now - self._last_update
        self._last_update = now

        # Check if we should generate a confabulation
        should_confabulate = (
            self._gap_detected and
            self._gap_severity >= self._confabulation_threshold and
            (now - self._last_confabulation_time) > self._confabulation_cooldown
        )

        if should_confabulate:
            # Generate confabulation to fill the gap
            narrative = self._generate_confabulation()
            confidence = self._calculate_narrative_confidence()

            self._recent_narrative = narrative
            self._narrative_confidence = confidence
            self._last_confabulation_time = now

            # Reset gap detection (until next gap)
            self._gap_detected = False
            self._gap_severity = 0.0

            # Publish the confabulation
            confabulation_state = ConfabulationState(
                timestamp=now,
                narrative=self._recent_narrative,
                confidence=confidence,
                gap_severity_prior=self._gap_severity,  # What triggered it
                is_confabulation=True,
                sources_used=self._get_recent_sources()
            )
            out = String()
            out.data = to_json(confabulation_state)
            self._pub.publish(out)

            self.get_logger().info(
                f"Confabulation Generated: '{self._recent_narrative[:50]}...' "
                f"(Confidence: {confidence:.2f})"
            )
        else:
            # No confabulation - publish current state or reset
            if self._recent_narrative:
                # Gradually decay confidence in existing narrative over time
                confidence_decay = 0.05 * dt  # 5% per second decay
                self._narrative_confidence = max(0.0, self._narrative_confidence - confidence_decay)
                if self._narrative_confidence < 0.2:
                    self._recent_narrative = ""  # Forget low-confidence narratives

            # Publish current state (may be empty)
            confabulation_state = ConfabulationState(
                timestamp=now,
                narrative=self._recent_narrative,
                confidence=self._narrative_confidence,
                gap_severity_prior=0.0,
                is_confabulation=False,
                sources_used=[]
            )
            out = String()
            out.data = to_json(confabulation_state)
            self._pub.publish(out)

        # Log gap status occasionally
        if self._gap_detected and int(now) % 3 == 0:  # Every 3 seconds when gap detected
            self.get_logger().debug(
                f"Narrative Gap - Severity:{self._gap_severity:.2f} "
                f"(Threshold:{self._confabulation_threshold:.2f})"
            )

    def _generate_confabulation(self) -> str:
        """Generate a confabulation to fill the detected narrative gap"""
        import random

        # Select bias-influenced components for the narrative
        templates = [
            "I remember {action} because {reason}",
            "It makes sense that {explanation}",
            "Actually, I {behavior} when {context}",
            "The reason for {event} is {cause}",
            "I {action} to achieve {goal}",
            "Based on past experience, {expectation}"
        ]

        # Bias-selected components
        actions = [
            "chose the safer option",
            "avoided the risky situation",
            "helped the person in need",
            "stood up for what's right",
            "learned from the experience",
            "made the best decision possible"
        ]

        reasons = [
            "it aligned with my values",
            "past experience showed it was wise",
            "I wanted to maintain consistency",
            "it was the most logical choice",
            "others would have done the same",
            "it felt intuitively correct"
        ]

        explanations = [
            "my subconscious had already processed it",
            "it fits with my established patterns",
            "there were subtle cues I picked up on",
            "it aligns with my long-term goals",
            "my intuition guided me toward it",
            "similar situations worked out well before"
        ]

        behaviors = [
            "paused to consider the consequences",
            "double-checked my understanding",
            "sought advice before acting",
            "took time to reflect",
            "followed proper procedures",
            "considered multiple perspectives"
        ]

        contexts = [
            "the situation was ambiguous",
            "there was conflicting information",
            "others were uncertain too",
            "it was a novel situation",
            "time pressure was involved",
            "emotions were running high"
        ]

        events = [
            "the outcome",
            "my reaction",
            "the decision point",
            "the turning point",
            "the moment of choice",
            "the critical juncture"
        ]

        causes = [
            "careful consideration of factors",
            "my values and priorities",
            "lessons from similar past events",
            "the desire to maintain integrity",
            "a commitment to consistency",
            "an unconscious bias toward fairness"
        ]

        goals = [
            "maintain my self-image",
            "preserve important relationships",
            "uphold my principles",
            "achieve long-term wellbeing",
            "avoid regret and guilt",
            "create positive outcomes"
        ]

        expectations = [
            "the pattern will continue",
            "similar situations will have similar outcomes",
            "my response was appropriate",
            "I handled it as well as could be expected",
            "the experience will inform future decisions",
            "I learned something valuable"
        ]

        # Select template and fill with bias-influenced components
        template = random.choice(templates)
        if "{action}" in template and "{reason}" in template:
            narrative = template.format(
                action=random.choice(actions),
                reason=random.choice(reasons)
            )
        elif "{explanation}" in template:
            narrative = template.format(
                explanation=random.choice(explanations)
            )
        elif "{behavior}" in template and "{context}" in template:
            narrative = template.format(
                behavior=random.choice(behaviors),
                context=random.choice(contexts)
            )
        elif "{event}" in template and "{cause}" in template:
            narrative = template.format(
                event=random.choice(events),
                cause=random.choice(causes)
            )
        elif "{action}" in template and "{goal}" in template:
            narrative = template.format(
                action=random.choice(actions),
                goal=random.choice(goals)
            )
        elif "{expectation}" in template:
            narrative = template.format(
                expectation=random.choice(expectations)
            )
        else:
            # Fallback
            narrative = "I believe this makes sense given what I know."

        # Apply biases to shape the narrative
        narrative = self._apply_biases(narrative)
        return narrative

    def _apply_biases(self, narrative: str) -> str:
        """Apply cognitive biases to shape the confabulation"""
        import random

        # Self-serving bias: make self look good
        if random.random() < self._self_serving_bias:
            # Add self-enhancing elements if not already present
            if not any(word in narrative.lower() for word in ['good', 'right', 'wise', 'best', 'correct']):
                enhancements = [
                    " which was the right thing to do",
                    " showing good judgment",
                    " reflecting my capabilities",
                    " demonstrating competence"
                ]
                narrative += random.choice(enhancements)

        # Coherence bias: make narrative more coherent
        if random.random() < self._coherence_bias:
            # Add connective elements for coherence
            if "because" not in narrative and "since" not in narrative:
                narrative = narrative.replace(". ", " because it fits with my understanding. ")

        # Familiarity bias: use familiar elements
        if random.random() < self._familiarity_bias:
            # Replace novel elements with familiar ones (simplified)
            pass  # In practice, would substitute unfamiliar concepts with familiar analogs

        # Optimism bias: tilt toward positive outcomes
        if random.random() < self._optimism_bias:
            # Add positive framing if not already present
            if not any(word in narrative.lower() for word in ['good', 'positive', 'benefit', 'gain', 'success']):
                positive_additions = [
                    " leading to positive outcomes",
                    " with beneficial consequences",
                    " resulting in growth",
                    " contributing to my development"
                ]
                narrative += random.choice(positive_additions)

        return narrative

    def _calculate_narrative_confidence(self) -> float:
        """Calculate confidence in the generated narrative"""
        # Base confidence from gap severity (bigger gap = less confident fill)
        base_confidence = max(0.1, 1.0 - self._gap_severity * 0.6)

        # Adjust for biases (more biases = lower epistemic confidence)
        bias_penalty = (
            self._self_serving_bias * 0.2 +
            (1.0 - self._coherence_bias) * 0.1 +
            self._familiarity_bias * 0.1 +
            self._optimism_bias * 0.1
        )
        confidence = base_confidence * (1.0 - bias_penalty)

        # Confidence decreases with time since last solid memory
        time_since_clear_narrative = getattr(self, '_time_since_clear_narrative', 0.0)
        time_penalty = min(0.5, time_since_clear_narrative * 0.01)
        confidence = max(0.1, confidence - time_penalty)

        return min(0.9, confidence)  # Cap confidence (never fully certain in confabulation)

    def _get_recent_sources(self) -> list:
        """Get recent gap sources for transparency"""
        if not hasattr(self, '_recent_gap_sources'):
            return []
        # Return sanitized source info
        return [
            {
                'source': s['source'],
                'severity': round(s['severity'], 2),
                'age_seconds': round(time.time() - s['timestamp'], 1)
            }
            for s in self._recent_gap_sources[-3:]  # Last 3 sources
        ]


def main(args=None):
    rclpy.init(args=args)
    node = ConfabulationEngineNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()