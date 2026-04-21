"""
grace_agi/subconscious/future_self_simulator.py
Subconscious Layer — Future Self Simulator
Prospective Memory · Anticipatory Emotion
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.grace.utils.schemas import FutureSelfState, to_json


class FutureSelfSimulatorNode(Node):
    def __init__(self):
        super().__init__("grace_future_self_simulator")

        # ── Parameters ────────────────────────────────────────────────────────
        self.declare_parameter("update_hz", 0.1)  # Prospective simulation runs slowly
        self.update_hz = self.get_parameter("update_hz").value

        # ── Internal State ───────────────────────────────────────────────────
        self._prospective_memory = {}        # Future events we're preparing for
        self._anticipatory_emotion = 0.0     # Current anticipatory emotional state
        self._optimism_bias = 0.6            # Tendency to overestimate positive outcomes
        self._pessimism_bias = 0.3           # Tendency to underestimate negative outcomes
        self._last_update = time.time()
        self._simulation_horizon = 86400.0   # Simulate up to 1 day ahead (seconds)

        # ── Prospective Memory Parameters ────────────────────────────────────
        self._memory_decay_rate = 0.001      # How fast prospective memories fade
        self._importance_threshold = 0.3     # Minimum importance to store in prospective memory
        self._emotional_salience_weight = 0.4 # How much emotion affects memory importance

        # ── Subscribers (Inputs from other systems) ─────────────────────────
        # Current goals and plans from conscious layer
        self.create_subscription(String, "/grace/conscious/executive_plan",
                                 self._on_executive_plan, 10)
        # Emotional state influences anticipation
        self.create_subscription(String, "/grace/unconscious/affective_state",
                                 self._on_affective_state, 10)
        # Reward predictions shape future expectations
        self.create_subscription(String, "/grace/unconscious/reward_signal",
                                 self._on_reward_signal, 10)
        # Threat assessments shape negative future simulations
        self.create_subscription(String, "/grace/vital/immune_budget",
                                 self._on_threat_budget, 10)
        # Autobiographical memory informs future simulations
        self.create_subscription(String, "/grace/subconscious/autobiographical_memory",
                                 self._on_autobiographical_memory, 10)

        # ── Publishers (Outputs to other systems) ───────────────────────────
        self._pub = self.create_publisher(String, "/grace/subconscious/future_self_state", 10)
        self.create_timer(1.0 / self.update_hz, self._update_future_self)
        self.get_logger().info("Future Self Simulator ready.")

    # ── Input Processing ─────────────────────────────────────────────────────
    def _on_executive_plan(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Executive plans become prospective memories
            goal = data.get("goal", "")
            steps = data.get("steps", [])
            priority = data.get("priority", 0.5)
            moral_cleared = data.get("moral_cleared", True)

            if goal and priority > self._importance_threshold:
                # Create a prospective memory entry
                event_id = f"goal_{int(time.time() * 1000)}_{len(self._prospective_memory)}"
                # Estimate completion time based on steps
                estimated_duration = len(steps) * 30.0  # Rough estimate: 30s per step
                event_time = time.time() + estimated_duration

                self._prospective_memory[event_id] = {
                    'type': 'goal',
                    'goal': goal,
                    'steps': steps,
                    'priority': priority,
                    'moral_cleared': moral_cleared,
                    'event_time': event_time,
                    'importance': priority,
                    'emotional_valence': 0.0,  # Will be updated by affective inputs
                    'created_at': time.time()
                }
        except Exception as e:
            self.get_logger().warn(f"Failed to process executive plan: {e}")

    def _on_affective_state(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Current affective state influences anticipatory emotion for future events
            valence = data.get("valence", 0.5)   # 0=negative  1=positive
            arousal = data.get("arousal", 0.3)   # 0=calm  1=excited

            # Update emotional valence of recent prospective memories
            current_time = time.time()
            for event_id, memory in self._prospective_memory.items():
                # Only update memories that are still relevant (not too far in future)
                time_to_event = memory['event_time'] - current_time
                if 0 < time_to_event < self._simulation_horizon:
                    # Recent memories are more influenced by current affect
                    recency_factor = max(0.0, 1.0 - (time_to_event / self._simulation_horizon))
                    emotion_influence = (valence - 0.5) * 2.0 * recency_factor * 0.3  # Convert to -1 to 1 range
                    memory['emotional_valence'] = max(-1.0, min(1.0,
                        memory['emotional_valence'] + emotion_influence))
        except Exception as e:
            self.get_logger().warn(f"Failed to process affective state: {e}")

    def _on_reward_signal(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Reward signals shape positive future expectations
            reward_value = data.get("value", 0.0)  # -1 to +1
            source = data.get("source", "unknown")

            # Positive rewards increase optimism about similar future events
            if reward_value > 0.3:
                optimism_boost = reward_value * 0.2
                self._optimism_bias = min(0.9, self._optimism_bias + optimism_boost)
            elif reward_value < -0.3:
                # Negative rewards increase pessimism
                pessimism_boost = abs(reward_value) * 0.2
                self._pessimism_bias = min(0.8, self._pessimism_bias + pessimism_boost)
        except Exception as e:
            self.get_logger().warn(f"Failed to process reward signal: {e}")

    def _on_threat_budget(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Threat assessments increase negative anticipatory emotion
            threat_level = data.get("relational_threat_budget", 0.0)
            if threat_level > 0.5:
                # Increase pessimism bias when threat is high
                threat_effect = (threat_level - 0.5) * 0.4
                self._pessimism_bias = min(0.8, self._pessimism_bias + threat_effect)
                # Slightly reduce optimism when threatened
                self._optimism_bias = max(0.3, self._optimism_bias - threat_effect * 0.3)
        except Exception as e:
            self.get_logger().warn(f"Failed to process threat budget: {e}")

    def _on_autobiographical_memory(self, msg: String):
        try:
            data = json.loads(msg.data)
            # Autobiographical memory provides templates for future simulation
            memory_content = data.get("content", "")
            emotional_tag = data.get("emotional_tag", 0.0)  # -1 to 1
            importance = data.get("importance", 0.5)

            # Use past emotional experiences to inform future simulations
            if importance > self._importance_threshold and abs(emotional_tag) > 0.2:
                # Slightly bias future simulations based on similar past emotional experiences
                emotion_influence = emotional_tag * 0.1
                # Apply to recent prospective memories
                current_time = time.time()
                for event_id, memory in self._prospective_memory.items():
                    time_to_event = memory['event_time'] - current_time
                    if 0 < time_to_event < self._simulation_horizon:
                        recency_factor = max(0.0, 1.0 - (time_to_event / self._simulation_horizon))
                        memory['emotional_valence'] = max(-1.0, min(1.0,
                            memory['emotional_valence'] + emotion_influence * recency_factor))
        except Exception as e:
            self.get_logger().warn(f"Failed to process autobiographical memory: {e}")

    # ── Future Self Dynamics Update ─────────────────────────────────────────
    def _update_future_self(self):
        now = time.time()
        dt = now - self._last_update
        self._last_update = now

        # Decay old prospective memories
        expired_memories = []
        for event_id, memory in self._prospective_memory.items():
            # Apply memory decay
            age = now - memory['created_at']
            decay_factor = self._memory_decay_rate * age
            memory['importance'] = max(0.0, memory['importance'] - decay_factor)

            # Remove expired memories (too old or too low importance)
            if (now - memory['created_at']) > (self._simulation_horizon * 2) or \
               memory['importance'] < self._importance_threshold * 0.5:
                expired_memories.append(event_id)

        # Remove expired memories
        for event_id in expired_memories:
            del self._prospective_memory[event_id]

        # Calculate anticipatory emotion based on prospective memories
        self._anticipatory_emotion = self._calculate_anticipatory_emotion(now)

        # Prepare outputs for publishing
        upcoming_events = self._get_upcoming_events(now)

        # Publish future self state
        future_self_state = FutureSelfState(
            timestamp=now,
            prospective_memory_count=len(self._prospective_memory),
            anticipatory_emotion=self._anticipatory_emotion,
            optimism_bias=self._optimism_bias,
            pessimism_bias=self._pessimism_bias,
            upcoming_events=upcoming_events,
            simulation_horizon=self._simulation_horizon
        )
        out = String()
        out.data = to_json(future_self_state)
        self._pub.publish(out)

        # Log status occasionally
        if int(now) % 30 == 0:  # Every 30 seconds
            self.get_logger().info(
                f"Future Self - Prospective:{len(self._prospective_memory)} "
                f"AnticipEmot:{self._anticipatory_emotion:.2f} "
                f"Optimism:{self._optimism_bias:.2f} "
                f"Pessimism:{self._pessimism_bias:.2f}"
            )

    def _calculate_anticipatory_emotion(self, now: float) -> float:
        """Calculate overall anticipatory emotional state"""
        if not self._prospective_memory:
            return 0.0

        total_weighted_emotion = 0.0
        total_importance = 0.0

        for memory in self._prospective_memory.values():
            # Weight by importance and temporal proximity
            time_to_event = memory['event_time'] - now
            if time_to_event > 0:  # Only future events
                temporal_weight = max(0.0, 1.0 - (time_to_event / self._simulation_horizon))
                importance_weight = memory['importance'] * temporal_weight
                emotion_contribution = memory['emotional_valence'] * importance_weight
                total_weighted_emotion += emotion_contribution
                total_importance += importance_weight

        if total_importance > 0:
            raw_emotion = total_weighted_emotion / total_importance
            # Apply optimism/pessimism biases
            if raw_emotion > 0:  # Positive anticipation
                biased_emotion = raw_emotion * (1.0 + self._optimism_bias * 0.5)
            else:  # Negative anticipation
                biased_emotion = raw_emotion * (1.0 + self._pessimism_bias * 0.5)
            return max(-1.0, min(1.0, biased_emotion))
        else:
            return 0.0

    def _get_upcoming_events(self, now: float) -> list:
        """Get list of upcoming events for publishing"""
        upcoming = []
        current_time = now
        horizon_end = current_time + self._simulation_horizon

        for event_id, memory in self._prospective_memory.items():
            event_time = memory['event_time']
            if current_time < event_time <= horizon_end:
                # Event is upcoming within our simulation horizon
                time_until = event_time - current_time
                upcoming.append({
                    'event_id': event_id,
                    'type': memory['type'],
                    'goal': memory.get('goal', ''),
                    'importance': memory['importance'],
                    'emotional_valence': memory['emotional_valence'],
                    'time_until_seconds': time_until,
                    'steps_count': len(memory.get('steps', []))
                })

        # Sort by time until event (soonest first)
        upcoming.sort(key=lambda x: x['time_until_seconds'])
        return upcoming[:10]  # Limit to top 10 upcoming events


def main(args=None):
    rclpy.init(args=args)
    node = FutureSelfSimulatorNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()