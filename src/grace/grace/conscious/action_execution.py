"""
grace_agi/conscious/action_execution.py
Action Execution + Expression + Social Behavior.

Translates ExecutivePlan steps into concrete ROS2 commands:
  - navigate_to_pose  → publishes geometry_msgs/PoseStamped on /goal_pose
  - take_photo        → publishes trigger on /grace/camera/trigger
  - speak             → publishes text on /grace/speech/out
  - avoid_obstacle    → publishes Twist on /cmd_vel
  - greet_person      → speak + gentle approach
  - wait              → no-op with log
  - return_home       → navigate to home pose

Feeds back into WorkingMemory, attitudes, social cognition, and affective
core by publishing to /grace/action/log.
"""
import json, time, math
import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Bool
from geometry_msgs.msg import PoseStamped, Twist
from rclpy.qos import QoSProfile, ReliabilityPolicy


class ActionExecutionNode(Node):

    HOME_POSE = {"x": 0.0, "y": 0.0, "yaw": 0.0}   # map frame home

    def __init__(self):
        super().__init__("grace_action_execution")

        self.declare_parameter("action_hz", 5.0)
        hz = self.get_parameter("action_hz").value

        self._pending_plan: dict = {}
        self._executing    = False
        self._blocked      = False

        # ── Subscribers ───────────────────────────────────────────────────────
        self.create_subscription(String, "/grace/conscious/executive_plan",
                                 self._on_plan,    10)
        self.create_subscription(String, "/grace/conscience/verdict",
                                 self._on_verdict, 10)

        # ── Publishers ────────────────────────────────────────────────────────
        self._pub_goal    = self.create_publisher(PoseStamped, "/goal_pose",              10)
        self._pub_vel     = self.create_publisher(Twist,        "/cmd_vel",               10)
        self._pub_speech  = self.create_publisher(String,       "/grace/speech/out",      10)
        self._pub_photo   = self.create_publisher(Bool,         "/grace/camera/trigger",  10)
        self._pub_log     = self.create_publisher(String,       "/grace/action/log",      10)

        self.create_timer(1.0 / hz, self._execute)
        self.get_logger().info("ActionExecution ready.")

    # ── Intake ────────────────────────────────────────────────────────────────

    def _on_plan(self, msg: String):
        try:
            plan = json.loads(msg.data)
            if not self._executing:
                self._pending_plan = plan
        except Exception: pass

    def _on_verdict(self, msg: String):
        try:
            v = json.loads(msg.data)
            self._blocked = v.get("block_action", False)
            if self._blocked:
                self.get_logger().warn(
                    f"ActionExecution: BLOCKED by Conscience — {v.get('reasoning','')[:80]}")
        except Exception: pass

    # ── Execution loop ────────────────────────────────────────────────────────

    def _execute(self):
        if self._blocked or not self._pending_plan:
            return

        plan  = self._pending_plan
        steps = plan.get("steps", [])
        if not steps:
            return

        self._executing = True
        step   = steps[0]
        action = step.get("action", "")
        params = step.get("params", {})

        try:
            if   action == "navigate_to_pose":  self._navigate(params)
            elif action == "take_photo":         self._take_photo(params)
            elif action == "speak":              self._speak(params)
            elif action == "avoid_obstacle":     self._avoid(params)
            elif action == "greet_person":       self._greet(params)
            elif action == "return_home":        self._navigate(self.HOME_POSE)
            elif action == "wait":               pass   # deliberate no-op
            else:
                self.get_logger().warn(f"ActionExecution: unknown action '{action}'")

            self._log(action, params, plan.get("goal", ""))
        except Exception as e:
            self.get_logger().error(f"ActionExecution error [{action}]: {e}")
        finally:
            self._executing    = False
            self._pending_plan = {}

    # ── Action implementations ────────────────────────────────────────────────

    def _navigate(self, params: dict):
        pose = PoseStamped()
        pose.header.frame_id = "map"
        pose.header.stamp    = self.get_clock().now().to_msg()
        pose.pose.position.x = float(params.get("x", 0.0))
        pose.pose.position.y = float(params.get("y", 0.0))

        # Convert yaw → quaternion (z, w only for 2D)
        yaw = float(params.get("yaw", 0.0))
        pose.pose.orientation.z = math.sin(yaw / 2.0)
        pose.pose.orientation.w = math.cos(yaw / 2.0)

        self._pub_goal.publish(pose)
        self.get_logger().info(
            f"Navigate → ({params.get('x',0):.2f}, {params.get('y',0):.2f})")

    def _take_photo(self, params: dict):
        trigger = Bool()
        trigger.data = True
        self._pub_photo.publish(trigger)
        self.get_logger().info(
            f"Photo trigger — subject: {params.get('subject', 'unknown')}")

    def _speak(self, params: dict):
        text = params.get("text", params.get("message", ""))
        if text:
            out = String(); out.data = text
            self._pub_speech.publish(out)
            self.get_logger().info(f"GRACE speaks: {text[:60]}")

    def _avoid(self, params: dict):
        twist = Twist()
        direction = params.get("direction", "backward")
        speed     = float(params.get("speed", 0.15))
        if direction == "backward":
            twist.linear.x = -speed
        elif direction == "left":
            twist.angular.z = speed
        elif direction == "right":
            twist.angular.z = -speed
        self._pub_vel.publish(twist)

        # Stop after brief evasion
        self.create_timer(0.8, lambda: self._pub_vel.publish(Twist()))
        self.get_logger().info(f"Obstacle avoidance: {direction}")

    def _greet(self, params: dict):
        greeting = params.get("text", "Hello! I am GRACE, a photography robot.")
        self._speak({"text": greeting})
        # Gentle approach
        twist = Twist(); twist.linear.x = 0.1
        self._pub_vel.publish(twist)
        self.create_timer(1.5, lambda: self._pub_vel.publish(Twist()))

    # ── Logging ───────────────────────────────────────────────────────────────

    def _log(self, action: str, params: dict, goal: str):
        out = String()
        out.data = json.dumps({
            "action":    action,
            "params":    params,
            "goal":      goal,
            "timestamp": time.time(),
        })
        self._pub_log.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = ActionExecutionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
