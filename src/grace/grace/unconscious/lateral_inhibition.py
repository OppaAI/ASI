"""
grace_agi/unconscious/lateral_inhibition.py
Unconscious Layer — Lateral Inhibition
Winner-take-all competition between neural signals
"""
import json, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from grace.utils.schemas import LateralInhibitionState, to_json


class LateralInhibitionNode(Node):
    def __init__(self):
        super().__init__("grace_lateral_inhibition")

        self.declare_parameter("update_hz", 2.0)
        self.update_hz = self.get_parameter("update_hz").value

        self._competitors = {}
        self._winning_signal = ""
        self._inhibition_strength = 0.0
        self._winner_salience = 0.0
        self._last_update = time.time()

        self.create_subscription(String, "/grace/unconscious/relevance",
                                 self._on_relevance, 10)
        self.create_subscription(String, "/grace/unconscious/thalamic_broadcast",
                                 self._on_thalamic_broadcast, 10)

        self._pub = self.create_publisher(String, "/grace/unconscious/lateral_inhibition", 10)
        self.create_timer(1.0 / self.update_hz, self._update_inhibition)
        self.get_logger().info("Lateral Inhibition ready.")

    def _on_relevance(self, msg: String):
        try:
            data = json.loads(msg.data)
            content = data.get("content", "unknown")
            score = data.get("score", 0.0)
            self._competitors[content] = {"score": score, "age": 0}
        except Exception as e:
            self.get_logger().warn(f"Failed to process relevance: {e}")

    def _on_thalamic_broadcast(self, msg: String):
        try:
            data = json.loads(msg.data)
            content = data.get("content", "unknown")
            salience = data.get("salience", 0.0)
            key = f"thalamic_{content}"
            self._competitors[key] = {"score": salience, "age": 0}
        except Exception as e:
            self.get_logger().warn(f"Failed to process thalamic broadcast: {e}")

    def _update_inhibition(self):
        now_t = time.time()
        dt = now_t - self._last_update
        self._last_update = now_t

        stale = []
        for sig, info in self._competitors.items():
            info["age"] = info.get("age", 0) + dt
            info["score"] = max(0.0, info["score"] - info["age"] * 0.05)
            if info["score"] <= 0.01:
                stale.append(sig)
        for sig in stale:
            del self._competitors[sig]

        competition_active = len(self._competitors) > 1
        num_competitors = len(self._competitors)

        if self._competitors:
            winner = max(self._competitors.items(), key=lambda x: x[1]["score"])
            self._winning_signal = winner[0]
            self._winner_salience = winner[1]["score"]
            if competition_active:
                runner_up_scores = sorted(
                    [v["score"] for v in self._competitors.values()], reverse=True)
                if len(runner_up_scores) > 1:
                    gap = runner_up_scores[0] - runner_up_scores[1]
                    self._inhibition_strength = min(1.0, max(0.0, gap * 2.0))
                else:
                    self._inhibition_strength = 0.0
            else:
                self._inhibition_strength = 0.0
        else:
            self._winning_signal = ""
            self._winner_salience = 0.0
            self._inhibition_strength = 0.0

        out = LateralInhibitionState(
            timestamp=now_t,
            competition_active=competition_active,
            winning_signal=self._winning_signal,
            inhibition_strength=self._inhibition_strength,
            num_competitors=num_competitors,
            winner_salience=self._winner_salience,
        )
        msg = String()
        msg.data = to_json(out)
        self._pub.publish(msg)

        if int(now_t) % 10 == 0:
            self.get_logger().info(
                f"Lateral Inh - winner:{self._winning_signal} "
                f"salience:{self._winner_salience:.2f} "
                f"competitors:{num_competitors}"
            )


def main(args=None):
    rclpy.init(args=args)
    node = LateralInhibitionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
