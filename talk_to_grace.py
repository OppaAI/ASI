#!/usr/bin/env python3
"""
talk_to_grace.py
Split-screen terminal UI:
  ┌─────────────────────────────────┐
  │  GRACE status panel (fixed)     │
  │  💭 inner thought               │
  │  🧠 global workspace            │
  │  ⚖️  conscience                  │
  ├─────────────────────────────────┤
  │  chat scrolls here              │
  │  ...                            │
  │  You: hi                        │
  │  GRACE: hey                     │
  └─────────────────────────────────┘
"""
import json
import threading
import time
import os
import shutil

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


# ── ANSI codes ────────────────────────────────────────────────────────────────
CYAN    = "\033[96m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
MAGENTA = "\033[95m"
RED     = "\033[91m"
RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"

def move(row, col=1):    return f"\033[{row};{col}H"
def clear_line():        return "\033[2K"
def save_cursor():       return "\033[s"
def restore_cursor():    return "\033[u"
def hide_cursor():       return "\033[?25l"
def show_cursor():       return "\033[?25h"
def clear_screen():      return "\033[2J"
def set_scroll(top, bot): return f"\033[{top};{bot}r"

# ── Status panel is 6 lines tall + 1 separator ────────────────────────────────
PANEL_LINES = 6


class GraceChat(Node):
    def __init__(self):
        super().__init__("grace_chat")

        self._pub_audio  = self.create_publisher(String, "/grace/audio/in",  10)
        self._pub_bundle = self.create_publisher(String, "/grace/sensors/bundle", 10)

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

        self._last_speech    = ""
        self._last_monologue = ""
        self._last_gw        = ""
        self._emotion        = "serene"
        self._conscience     = ""
        self._waiting        = False
        self._lock           = threading.Lock()

    # ── Panel update — writes into the fixed top area ─────────────────────────

    def _update_panel(self):
        w = shutil.get_terminal_size((80, 24)).columns
        with self._lock:
            out = save_cursor()

            # Row 1 — header
            out += move(1)
            out += clear_line()
            out += f"{CYAN}{BOLD}  GRACE  {RESET}{DIM}{'─' * (w - 8)}{RESET}"

            # Row 2 — emotion
            out += move(2)
            out += clear_line()
            out += f"{MAGENTA}  ❤  {self._emotion:<20}{RESET}"

            # Row 3 — inner thought
            mono = self._last_monologue[:w - 6] if self._last_monologue else "..."
            out += move(3)
            out += clear_line()
            out += f"{DIM}  💭  {mono}{RESET}"

            # Row 4 — global workspace
            gw = self._last_gw[:w - 6] if self._last_gw else "..."
            out += move(4)
            out += clear_line()
            out += f"{DIM}  🧠  {gw}{RESET}"

            # Row 5 — conscience
            cs = self._conscience[:w - 6] if self._conscience else "clear"
            out += move(5)
            out += clear_line()
            out += f"{YELLOW}  ⚖   {cs}{RESET}"

            # Row 6 — separator
            out += move(6)
            out += clear_line()
            out += f"{DIM}{'─' * w}{RESET}"

            out += restore_cursor()
            print(out, end="", flush=True)

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _on_speech(self, msg: String):
        text = msg.data.strip()
        if text and text != self._last_speech:
            self._last_speech = text
            self._chat_print(f"{GREEN}{BOLD}GRACE:{RESET} {GREEN}{text}{RESET}\n")
            self._waiting = False

    def _on_reflection(self, msg: String):
        try:
            d = json.loads(msg.data)
            mono = d.get("inner_monologue", "").strip()
            if mono and mono != self._last_monologue:
                self._last_monologue = mono
                self._update_panel()
        except Exception:
            pass

    def _on_gw(self, msg: String):
        try:
            d = json.loads(msg.data)
            broadcast = d.get("broadcast", "")
            salience  = d.get("salience", 0)
            if salience > 0.3 and broadcast and broadcast != self._last_gw:
                self._last_gw = f"[{salience:.2f}] {broadcast}"
                self._update_panel()
        except Exception:
            pass

    def _on_affect(self, msg: String):
        try:
            d = json.loads(msg.data)
            emotion = d.get("emotion_label", "neutral")
            if emotion != self._emotion:
                self._emotion = emotion
                self._update_panel()
        except Exception:
            pass

    def _on_verdict(self, msg: String):
        try:
            d = json.loads(msg.data)
            if d.get("block_action"):
                self._conscience = f"VETO — {d.get('reasoning','')[:50]}"
            else:
                self._conscience = f"{d.get('verdict','?')} ({d.get('confidence',0):.2f})"
            self._update_panel()
        except Exception:
            pass

    # ── Chat print — writes into the scrolling area ───────────────────────────

    def _chat_print(self, text: str):
        with self._lock:
            print(text, flush=True)

    # ── Send ──────────────────────────────────────────────────────────────────

    def send(self, text: str):
        audio_msg = String()
        audio_msg.data = text
        self._pub_audio.publish(audio_msg)

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

    t = threading.Thread(target=spin_thread, args=(node,), daemon=True)
    t.start()

    rows = shutil.get_terminal_size((80, 24)).lines

    # Clear screen and set up scroll region below the panel
    print(hide_cursor(), end="")
    print(clear_screen(), end="")
    print(set_scroll(PANEL_LINES + 1, rows), end="", flush=True)

    # Draw initial panel
    node._update_panel()

    # Move cursor into chat area
    print(move(PANEL_LINES + 1), end="", flush=True)
    print(f"{DIM}  Connecting to GRACE...{RESET}", flush=True)

    time.sleep(1.0)
    node._update_panel()

    try:
        while True:
            # Input prompt lives in chat area
            print(move(rows), end="", flush=True)
            try:
                emotion = node._emotion
                prompt = f"{CYAN}{BOLD}You [{emotion}]:{RESET} "
                print(prompt, end="", flush=True)
                print(show_cursor(), end="", flush=True)
                user_input = input("").strip()
                print(hide_cursor(), end="", flush=True)
            except EOFError:
                break

            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit", "bye"):
                break

            # Echo input into chat scroll area
            node._chat_print(
                f"{CYAN}You [{emotion}]:{RESET} {user_input}")

            node.send(user_input)

            deadline = time.time() + 20.0
            while node._waiting and time.time() < deadline:
                time.sleep(0.1)

            if node._waiting:
                node._chat_print(
                    f"{YELLOW}  (still thinking...){RESET}")
                node._waiting = False

    except KeyboardInterrupt:
        pass

    # Restore terminal
    print(show_cursor(), end="")
    print(set_scroll(1, rows), end="")
    print(clear_screen(), end="", flush=True)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()