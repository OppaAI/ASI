"""
grace_agi/unconscious/cognitive_bias.py
Unconscious Layer — Cognitive Biases
Confirmation · Availability · Anchoring · Optimism · Negativity · In-group
Neuromodulatory influence distorts retrieval through biased processing.
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.utils.schemas import CognitiveBiasState, to_json


class CognitiveBiasNode(Node):
    def __init__(self):
        super().__init__("grace_cognitive_bias")

        self.declare_parameter("update_hz", 2.0)
        self.update_hz = self.get_parameter("update_hz").value

        self._confirmation_bias = 0.3
        self._availability_bias = 0.3
        self._anchoring_bias = 0.2
        self._optimism_bias = 0.5
        self._negativity_bias = 0.3
        self._in_group_bias = 0.2
        self._dominant_bias = "confirmation"
        self._neuromod_influence = 0.3
        self._last_update = time.time()

        self.create_subscription(String, "/grace/unconscious/neuromodulatory",
                                 self._on_neuromodulatory, 10)

        self._pub = self.create_publisher(String, "/grace/unconscious/cognitive_bias", 10)
        self.create_timer(1.0 / self.update_hz, self._update_biases)
        self.get_logger().info("Cognitive Bias ready.")

    def _on_neuromodulatory(self, msg: String):
        try:
            data = json.loads(msg.data)
            dopamine = data.get("dopamine", 0.5)
            cortisol = data.get("cortisol", 0.3)
            serotonin = data.get("serotonin", 0.6)
            norepinephrine = data.get("norepinephrine", 0.4)

            self._neuromod_influence = (norepinephrine * 0.4 + cortisol * 0.3 +
                                        dopamine * 0.2 + (1.0 - serotonin) * 0.1)

            self._optimism_bias = max(0.0, min(1.0,
                self._optimism_bias + (dopamine - 0.5) * 0.4))
            self._negativity_bias = max(0.0, min(1.0,
                self._negativity_bias + (cortisol - 0.3) * 0.5))
            self._confirmation_bias = max(0.0, min(1.0,
                self._confirmation_bias + (serotonin - 0.6) * 0.3))
            self._availability_bias = max(0.0, min(1.0,
                self._availability_bias + norepinephrine * 0.2))
        except Exception as e:
            self.get_logger().warn(f"Failed to process neuromodulatory: {e}")

    def _update_biases(self):
        now_t = time.time()
        dt = now_t - self._last_update
        self._last_update = now_t

        biases = {
            "confirmation": self._confirmation_bias,
            "availability": self._availability_bias,
            "anchoring": self._anchoring_bias,
            "optimism": self._optimism_bias,
            "negativity": self._negativity_bias,
            "in_group": self._in_group_bias,
        }
        self._dominant_bias = max(biases, key=biases.get)

        out = CognitiveBiasState(
            timestamp=now_t,
            confirmation_bias=self._confirmation_bias,
            availability_bias=self._availability_bias,
            anchoring_bias=self._anchoring_bias,
            optimism_bias=self._optimism_bias,
            negativity_bias=self._negativity_bias,
            in_group_bias=self._in_group_bias,
            current_dominant_bias=self._dominant_bias,
            neuromodulatory_influence=self._neuromod_influence,
        )
        msg = String()
        msg.data = to_json(out)
        self._pub.publish(msg)

        if int(now_t) % 10 == 0:
            self.get_logger().info(
                f"Bias dominant:{self._dominant_bias} "
                f"conf:{self._confirmation_bias:.2f} "
                f"opt:{self._optimism_bias:.2f} "
                f"neg:{self._negativity_bias:.2f}"
            )


def main(args=None):
    rclpy.init(args=args)
    node = CognitiveBiasNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
