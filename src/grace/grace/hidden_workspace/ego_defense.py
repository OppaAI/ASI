"""
grace_agi/hidden_workspace/ego_defense.py
Hidden Workspace — Ego Defense Mechanisms
Rule-based system tracking repression, rationalization, projection, denial.
"""
import json
import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.utils.schemas import EgoDefenseState, to_json


DEFENSE_NAMES = ["repression_level", "rationalization_level",
                 "projection_level", "denial_level"]

DECAY_RATES = {
    "repression_level": 0.03,
    "rationalization_level": 0.05,
    "projection_level": 0.04,
    "denial_level": 0.06,
}

BASELINE = {
    "repression_level": 0.2,
    "rationalization_level": 0.3,
    "projection_level": 0.1,
    "denial_level": 0.1,
}


class EgoDefenseNode(Node):
    def __init__(self):
        super().__init__("grace_ego_defense")

        self.declare_parameter("update_hz", 0.5)
        self.update_hz = self.get_parameter("update_hz").value

        self._defenses = dict(BASELINE)
        self._last_update = time.time()
        self._under_threat = False
        self._pain_intensity = 0.0
        self._error_severity = 0.0
        self._reflection_load = 0.0

        self.create_subscription(String, "/grace/unconscious/affective_state",
                                 self._on_affect, 10)
        self.create_subscription(String, "/grace/vital/pain_signal",
                                 self._on_pain, 10)
        self.create_subscription(String, "/grace/hidden/error_monitoring",
                                 self._on_error, 10)
        self.create_subscription(String, "/grace/hidden/private_reflection",
                                 self._on_reflection, 10)

        self._pub = self.create_publisher(String, "/grace/hidden/ego_defense", 10)
        self.create_timer(1.0 / self.update_hz, self._tick)
        self.get_logger().info("Ego Defense Mechanisms ready.")

    def _on_affect(self, msg: String):
        try:
            d = json.loads(msg.data)
            valence = d.get("valence", 0.5)
            arousal = d.get("arousal", 0.3)
            self._under_threat = valence < 0.35 and arousal > 0.5
        except Exception:
            pass

    def _on_pain(self, msg: String):
        try:
            self._pain_intensity = json.loads(msg.data).get("pain_intensity", 0.0)
        except Exception:
            pass

    def _on_error(self, msg: String):
        try:
            d = json.loads(msg.data)
            self._error_severity = max(
                d.get("error_severity", 0.0),
                d.get("conflict_severity", 0.0),
            )
        except Exception:
            pass

    def _on_reflection(self, msg: String):
        try:
            self._reflection_load = json.loads(msg.data).get("cognitive_load", 0.0)
        except Exception:
            pass

    def _tick(self):
        now = time.time()
        dt = now - self._last_update
        self._last_update = now

        threat_level = max(
            self._pain_intensity,
            self._error_severity,
            0.3 if self._under_threat else 0.0,
        )

        for name in DEFENSE_NAMES:
            cur = self._defenses[name]
            base = BASELINE[name]
            decay = DECAY_RATES[name]

            if threat_level > 0.2:
                activation = threat_level * (0.15 if name == "projection_level" else 0.12)
                self._defenses[name] = min(0.9, cur + activation * dt)
            else:
                self._defenses[name] = max(base, cur - decay * dt)

        dom_def = max(self._defenses, key=self._defenses.get)
        dom_val = self._defenses[dom_def]
        for name in DEFENSE_NAMES:
            self._defenses[name] = round(max(0.0, min(0.95, self._defenses[name])), 3)

        defense_activation = sum(self._defenses[n] for n in DEFENSE_NAMES) / len(DEFENSE_NAMES)

        state = EgoDefenseState(
            timestamp=now,
            repression_level=self._defenses["repression_level"],
            rationalization_level=self._defenses["rationalization_level"],
            projection_level=self._defenses["projection_level"],
            denial_level=self._defenses["denial_level"],
            dominant_defense=dom_def.replace("_level", ""),
            defense_activation=round(defense_activation, 3),
        )
        out = String()
        out.data = to_json(state)
        self._pub.publish(out)

        if defense_activation > 0.6 and int(now) % 8 == 0:
            self.get_logger().warn(
                f"Defenses active: {dom_def}={dom_val:.2f} "
                f"overall={defense_activation:.2f}"
            )


def main(args=None):
    rclpy.init(args=args)
    node = EgoDefenseNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
