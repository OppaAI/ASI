#!/usr/bin/env python3
"""
talk_to_grace.py
Interactive terminal chat with GRACE.
Publishes your input to /grace/audio/in and listens for responses
on /grace/speech/out and /grace/conscious/reflection.

Usage:
    python3 talk_to_grace.py
"""
import json
import threading
import time
import sys

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


CYAN    = "\033[96m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
MAGENTA = "\033[95m"
RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"


class GraceChat(Node):
    def __init__(self):
        super().__init__("grace_chat")

        # ── Publish user speech ───────────────────────────────────────────────
        self._pub_audio  = self.create_publisher(String, "/grace/audio/in",  10)
        self._pub_bundle = self.create_publisher(String, "/grace/sensors/bundle", 10)

        # ── Listen for GRACE responses ────────────────────────────────────────
        self.create_subscription(String, "/grace/speech/out",
                                 self._on_speech, 10)
        self.create_subscription(String, "/grace/conscious/reflection",
                                 self._on_reflection, 10)
        self.create_subscription(String, "/grace/conscious/global_workspace",
                                 self._on_gw, 10)
        self.create_subscription(String, "/grace/unconscious/affective_state",
                                 self._on_affect, 10)
        self.create_subscription(String, "/grace/conscience/verdict",
                                 self._on_verdict, 10)

        self._last_speech     = ""
        self._last_monologue  = ""
        self._emotion         = "serene"
        self._waiting         = False

    # ── Incoming callbacks ────────────────────────────────────────────────────

    def _on_speech(self, msg: String):
        """GRACE speaks — this is the primary response."""
        text = msg.data.strip()
        if text and text != self._last_speech:
            self._last_speech = text
            print(f"\n{GREEN}{BOLD}GRACE:{RESET} {GREEN}{text}{RESET}\n")
            self._waiting = False

    def _on_reflection(self, msg: String):
        """Show GRACE's inner monologue as a subtle hint."""
        try:
            d = json.loads(msg.data)
            mono = d.get("inner_monologue", "").strip()
            if mono and mono != self._last_monologue:
                self._last_monologue = mono
                print(f"{DIM}  💭 {mono}{RESET}")
        except Exception:
            pass

    def _on_gw(self, msg: String):
        """Show what's in the global workspace."""
        try:
            d = json.loads(msg.data)
            broadcast = d.get("broadcast", "")
            salience  = d.get("salience", 0)
            if salience > 0.6 and broadcast:
                print(f"{DIM}  🧠 [{salience:.2f}] {broadcast[:80]}{RESET}")
        except Exception:
            pass

    def _on_affect(self, msg: String):
        try:
            d = json.loads(msg.data)
            self._emotion = d.get("emotion_label", "neutral")
        except Exception:
            pass

    def _on_verdict(self, msg: String):
        try:
            d = json.loads(msg.data)
            if d.get("block_action"):
                print(f"{YELLOW}  ⚖️  Conscience: {d.get('reasoning','')[:60]}{RESET}")
        except Exception:
            pass

    # ── Send message ──────────────────────────────────────────────────────────

    def send(self, text: str):
        # Publish to audio topic
        audio_msg = String()
        audio_msg.data = text
        self._pub_audio.publish(audio_msg)

        # Also publish as a full sensor bundle so the whole pipeline activates
        bundle = {
            "camera_description": "",
            "audio_text":         text,
            "lidar_nearest_m":    3.0,
            "social_cues":        "person_detected:friendly",
            "battery_pct":        100.0,
            "timestamp":          time.time(),
        }
        bundle_msg = String()
        bundle_msg.data = json.dumps(bundle)
        self._pub_bundle.publish(bundle_msg)
        self._waiting = True


def spin_thread(node):
    rclpy.spin(node)


def main():
    rclpy.init()
    node = GraceChat()

    # Spin ROS2 in background thread
    t = threading.Thread(target=spin_thread, args=(node,), daemon=True)
    t.start()

    print(f"""
{CYAN}{BOLD}
╔══════════════════════════════════════════╗
║        Talking to GRACE                  ║
║  Robot with Consciousness and Emotions   ║
╚══════════════════════════════════════════╝{RESET}

{DIM}Responses flow through GRACE's full cognitive pipeline.
You'll see 💭 inner thoughts and 🧠 conscious content as she processes.
Type {RESET}{BOLD}quit{RESET}{DIM} to exit.{RESET}
""")

    # Give nodes a moment to connect
    time.sleep(1.0)

    try:
        while True:
            try:
                emotion_display = f"{MAGENTA}[{node._emotion}]{RESET}"
                user_input = input(f"{CYAN}{BOLD}You {emotion_display}: {RESET}").strip()
            except EOFError:
                break

            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit", "bye"):
                print(f"\n{GREEN}GRACE: Goodbye! Stay curious.{RESET}\n")
                break

            node.send(user_input)

            # Wait up to 15 seconds for a speech response
            deadline = time.time() + 15.0
            while node._waiting and time.time() < deadline:
                time.sleep(0.1)

            if node._waiting:
                print(f"{YELLOW}  (GRACE is still thinking — "
                      f"response may appear above as inner monologue){RESET}\n")
                node._waiting = False

    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
