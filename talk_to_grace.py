#!/usr/bin/env python3
"""
talk_to_grace.py
Full-brain conversational interface.
Every message you send activates the complete cognitive pipeline:
sensors → unconscious → subconscious → conscious → conscience → action

Split-screen UI:
  ┌─────────────────────────────────────────────────────┐
  │  ❤  emotion    ⚡ arousal    🎯 salience   ⚖ verdict │
  │  💭  inner monologue (reflection)                    │
  │  🧠  global workspace broadcast                      │
  │  👁  qualia / phenomenal experience                  │
  │  🗄  memory context                                  │
  │  📋  executive plan                                  │
  ├─────────────────────────────────────────────────────┤
  │  scrolling chat                                      │
  └─────────────────────────────────────────────────────┘
"""
import json, threading, time, shutil, rclpy
from rclpy.node import Node
from std_msgs.msg import String

# ── ANSI ──────────────────────────────────────────────────────────────────────
CYAN    = "\033[96m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
MAGENTA = "\033[95m"
RED     = "\033[91m"
BLUE    = "\033[94m"
WHITE   = "\033[97m"
RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"

def move(r, c=1):      return f"\033[{r};{c}H"
def clr():             return "\033[2K"
def save():            return "\033[s"
def restore():         return "\033[u"
def hide_cur():        return "\033[?25l"
def show_cur():        return "\033[?25h"
def cls():             return "\033[2J"
def scroll(t, b):      return f"\033[{t};{b}r"

PANEL = 9   # number of fixed header lines


class GraceChat(Node):
    def __init__(self):
        super().__init__("grace_chat")

        # ── Publishers ────────────────────────────────────────────────────────
        self._pub_audio   = self.create_publisher(String, "/grace/audio/in",            10)
        self._pub_bundle  = self.create_publisher(String, "/grace/sensors/bundle",       10)
        self._pub_wm      = self.create_publisher(String, "/grace/conscious/working_memory", 10)
        self._pub_dream   = self.create_publisher(String, "/grace/dreaming/trigger",     10)

        # ── Brain state ───────────────────────────────────────────────────────
        self._emotion     = "serene"
        self._arousal     = 0.3
        self._valence     = 0.6
        self._salience    = 0.0
        self._monologue   = "..."
        self._conclusion  = ""
        self._broadcast   = "..."
        self._qualia      = "..."
        self._memory_ctx  = "..."
        self._plan        = ""
        self._verdict     = "neutral"
        self._verdict_conf= 0.0
        self._blocked     = False
        self._epi_count   = 0
        self._sem_count   = 0
        self._meta_conf   = 0.0
        self._dmn         = ""

        self._last_speech  = ""
        self._waiting      = False
        self._lock         = threading.Lock()

        # ── Subscriptions — every brain topic ─────────────────────────────────
        subs = [
            ("/grace/unconscious/affective_state",    self._on_affect),
            ("/grace/unconscious/reward",             self._on_reward),
            ("/grace/conscious/global_workspace",     self._on_gw),
            ("/grace/conscious/reflection",           self._on_reflection),
            ("/grace/conscious/metacognition",        self._on_meta),
            ("/grace/conscious/salience",             self._on_salience),
            ("/grace/conscious/executive_plan",       self._on_plan),
            ("/grace/conscious/memory_context",       self._on_memory),
            ("/grace/conscious/dmn",                  self._on_dmn),
            ("/grace/conscious/narrative_self",       self._on_narrative),
            ("/grace/qualia/field",                   self._on_qualia),
            ("/grace/conscience/verdict",             self._on_verdict),
            ("/grace/subconscious/episodic_recall",   self._on_episodic),
            ("/grace/subconscious/semantic_recall",   self._on_semantic),
            ("/grace/subconscious/social_recall",     self._on_social),
            ("/grace/speech/out",                     self._on_speech),
            ("/grace/action/log",                     self._on_action),
        ]
        for topic, cb in subs:
            self.create_subscription(String, topic, cb, 10)

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _on_affect(self, msg):
        try:
            d = json.loads(msg.data)
            with self._lock:
                self._emotion  = d.get("emotion_label", self._emotion)
                self._arousal  = d.get("arousal",  self._arousal)
                self._valence  = d.get("valence",  self._valence)
            self._redraw()
        except Exception: pass

    def _on_reward(self, msg):
        try:
            d = json.loads(msg.data)
            # reward shifts valence display subtly
            with self._lock:
                self._valence = max(0.0, min(1.0,
                    self._valence * 0.9 + (d.get("value", 0) + 1) / 2 * 0.1))
            self._redraw()
        except Exception: pass

    def _on_gw(self, msg):
        try:
            d = json.loads(msg.data)
            bc  = d.get("broadcast", "")
            sal = d.get("salience", 0)
            if bc:
                with self._lock:
                    self._broadcast = bc
                    self._salience  = sal
                self._redraw()
        except Exception: pass

    def _on_reflection(self, msg):
        try:
            d = json.loads(msg.data)
            mono = d.get("inner_monologue", "")
            conc = d.get("symbolic_conclusion", "")
            if mono:
                with self._lock:
                    self._monologue  = mono
                    self._conclusion = conc
                self._redraw()
        except Exception: pass

    def _on_meta(self, msg):
        try:
            d = json.loads(msg.data)
            with self._lock:
                self._meta_conf = d.get("confidence_in_own_reasoning", self._meta_conf)
            self._redraw()
        except Exception: pass

    def _on_salience(self, msg):
        try:
            d = json.loads(msg.data)
            sal = d.get("salience", 0)
            with self._lock:
                self._salience = max(self._salience, sal)
            self._redraw()
        except Exception: pass

    def _on_plan(self, msg):
        try:
            d = json.loads(msg.data)
            goal  = d.get("goal", "")
            steps = d.get("steps", [])
            action = steps[0].get("action", "") if steps else ""
            if goal:
                with self._lock:
                    self._plan = f"{action} → {goal[:60]}" if action else goal[:70]
                self._redraw()
        except Exception: pass

    def _on_memory(self, msg):
        try:
            d = json.loads(msg.data)
            bc = d.get("broadcast", "")
            if bc:
                with self._lock:
                    self._memory_ctx = bc
                self._redraw()
        except Exception: pass

    def _on_dmn(self, msg):
        try:
            d = json.loads(msg.data)
            sim = d.get("narrative_simulation", "")
            if sim:
                with self._lock:
                    self._dmn = sim
        except Exception: pass

    def _on_narrative(self, msg):
        try:
            d = json.loads(msg.data)
            # narrative self updates are slow — just note it fired
        except Exception: pass

    def _on_qualia(self, msg):
        try:
            d = json.loads(msg.data)
            pc = d.get("phenomenal_content", "")
            if pc:
                with self._lock:
                    self._qualia = pc
                self._redraw()
        except Exception: pass

    def _on_verdict(self, msg):
        try:
            d = json.loads(msg.data)
            with self._lock:
                self._verdict      = d.get("verdict", "neutral")
                self._verdict_conf = d.get("confidence", 0.0)
                self._blocked      = d.get("block_action", False)
            self._redraw()
            if self._blocked:
                self._chat_print(
                    f"{RED}{BOLD}  ⚖  CONSCIENCE VETO:{RESET} "
                    f"{RED}{d.get('reasoning','')[:70]}{RESET}")
        except Exception: pass

    def _on_episodic(self, msg):
        try:
            d = json.loads(msg.data)
            recalled = d.get("recalled", [])
            if recalled:
                with self._lock:
                    self._epi_count += 1
                self._chat_print(
                    f"{BLUE}{DIM}  🗄  Episodic recall: "
                    f"{str(recalled[0])[:80]}{RESET}")
        except Exception: pass

    def _on_semantic(self, msg):
        try:
            d = json.loads(msg.data)
            recalled = d.get("recalled", [])
            if recalled:
                with self._lock:
                    self._sem_count += 1
                self._chat_print(
                    f"{BLUE}{DIM}  📚  Semantic recall: "
                    f"{str(recalled[0])[:80]}{RESET}")
        except Exception: pass

    def _on_social(self, msg):
        try:
            d = json.loads(msg.data)
            gd = d.get("group_dynamic", "")
            if gd:
                self._chat_print(
                    f"{CYAN}{DIM}  👥  Social: {gd}{RESET}")
        except Exception: pass

    def _on_speech(self, msg):
        text = msg.data.strip()
        if text and text != self._last_speech:
            self._last_speech = text
            self._chat_print(f"\n{GREEN}{BOLD}GRACE:{RESET} {GREEN}{text}{RESET}\n")
            self._waiting = False

    def _on_action(self, msg):
        try:
            d = json.loads(msg.data)
            action = d.get("action", "")
            goal   = d.get("goal", "")
            if action and action != "speak":
                self._chat_print(
                    f"{YELLOW}{DIM}  ⚙  Action: {action}"
                    f"{f' → {goal[:40]}' if goal else ''}{RESET}")
        except Exception: pass

    # ── Panel ─────────────────────────────────────────────────────────────────

    def _redraw(self):
        w = shutil.get_terminal_size((100, 30)).columns

        def trunc(s, n): return str(s)[:n] if s else "..."

        # Emotion bar
        val_bar = int(self._valence * 10)
        aro_bar = int(self._arousal * 10)
        val_str = f"{'█' * val_bar}{'░' * (10 - val_bar)}"
        aro_str = f"{'█' * aro_bar}{'░' * (10 - aro_bar)}"

        # Verdict colour
        vc = RED if self._verdict == "immoral" else (
             GREEN if self._verdict == "moral" else YELLOW)

        out = save()
        out += move(1); out += clr()
        out += f"{CYAN}{BOLD}  GRACE  {RESET}"
        out += f"{DIM}valence {MAGENTA}{val_str}{RESET}  "
        out += f"{DIM}arousal {YELLOW}{aro_str}{RESET}  "
        out += f"{MAGENTA}{BOLD}{self._emotion:<12}{RESET}  "
        out += f"{DIM}meta:{GREEN}{self._meta_conf:.2f}{RESET}  "
        out += f"{DIM}sal:{CYAN}{self._salience:.2f}{RESET}  "
        out += f"{vc}⚖ {self._verdict}({self._verdict_conf:.2f}){RESET}"

        out += move(2); out += clr()
        out += f"{DIM}  💭  {MAGENTA}{trunc(self._monologue, w-8)}{RESET}"

        out += move(3); out += clr()
        if self._conclusion:
            out += f"{DIM}  ∴   {WHITE}{trunc(self._conclusion, w-8)}{RESET}"

        out += move(4); out += clr()
        out += f"{DIM}  🧠  {WHITE}{trunc(self._broadcast, w-8)}{RESET}"

        out += move(5); out += clr()
        out += f"{DIM}  👁   {MAGENTA}{trunc(self._qualia, w-8)}{RESET}"

        out += move(6); out += clr()
        out += f"{DIM}  🗄   {CYAN}{trunc(self._memory_ctx, w-8)}{RESET}"

        out += move(7); out += clr()
        out += f"{DIM}  📋  {GREEN}{trunc(self._plan, w-8)}{RESET}"

        out += move(8); out += clr()
        out += f"{DIM}  📖  epi×{self._epi_count}  sem×{self._sem_count}  "
        if self._dmn:
            out += f"dmn: {trunc(self._dmn, w-30)}"
        out += RESET

        out += move(9); out += clr()
        out += f"{DIM}{'─' * w}{RESET}"

        out += restore()
        print(out, end="", flush=True)

    # ── Chat print ────────────────────────────────────────────────────────────

    def _chat_print(self, text):
        with self._lock:
            print(text, flush=True)

    # ── Send — engages every brain region ────────────────────────────────────

    def send(self, text: str):
        # 1. Audio — triggers conversation node
        a = String(); a.data = text
        self._pub_audio.publish(a)

        # 2. Sensor bundle — triggers entire unconscious + subconscious pipeline
        bundle = {
            "camera_description": "person talking to GRACE, making eye contact",
            "audio_text":         text,
            "lidar_nearest_m":    1.5,
            "social_cues":        "person_detected:friendly",
            "battery_pct":        95.0,
            "timestamp":          time.time(),
        }
        b = String(); b.data = json.dumps(bundle)
        self._pub_bundle.publish(b)

        # 3. Working memory — triggers episodic + semantic recall
        wm = {
            "timestamp":     time.time(),
            "active_thought": text,
            "phonological":  [text[:80]],
            "visuospatial":  [],
        }
        w = String(); w.data = json.dumps(wm)
        self._pub_wm.publish(w)

        self._waiting = True


def spin_thread(node):
    rclpy.spin(node)


def main():
    rclpy.init()
    node = GraceChat()

    t = threading.Thread(target=spin_thread, args=(node,), daemon=True)
    t.start()

    rows = shutil.get_terminal_size((100, 30)).lines

    print(hide_cur(), end="")
    print(cls(), end="")
    print(scroll(PANEL + 1, rows), end="", flush=True)
    print(move(PANEL + 1), end="", flush=True)

    node._redraw()

    print(f"{DIM}  Connecting to GRACE...{RESET}", flush=True)
    time.sleep(1.5)
    node._redraw()

    try:
        while True:
            print(show_cur(), end="", flush=True)
            emotion = node._emotion
            prompt  = f"{CYAN}{BOLD}You [{emotion}]:{RESET} "
            print(prompt, end="", flush=True)

            try:
                user_input = input("").strip()
            except EOFError:
                break

            print(hide_cur(), end="", flush=True)

            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit", "bye"):
                node._chat_print(f"\n{GREEN}GRACE: Goodbye.{RESET}\n")
                break

            # Special commands
            if user_input.lower() == "/dream":
                d = String(); d.data = "{}"
                node._pub_dream.publish(d)
                node._chat_print(f"{DIM}  🌙  Dream cycle triggered...{RESET}")
                continue

            if user_input.lower() == "/status":
                node._chat_print(
                    f"{DIM}  Brain: emotion={node._emotion} "
                    f"arousal={node._arousal:.2f} "
                    f"salience={node._salience:.2f} "
                    f"epi_recalls={node._epi_count} "
                    f"sem_recalls={node._sem_count}{RESET}")
                continue

            # Echo input
            node._chat_print(
                f"{CYAN}You [{emotion}]:{RESET} {user_input}")

            node.send(user_input)

            # Wait for speech response
            deadline = time.time() + 20.0
            while node._waiting and time.time() < deadline:
                time.sleep(0.1)

            if node._waiting:
                node._chat_print(
                    f"{YELLOW}  (GRACE is still processing...){RESET}")
                node._waiting = False

    except KeyboardInterrupt:
        pass

    print(show_cur(), end="")
    print(scroll(1, rows), end="")
    print(cls(), end="", flush=True)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()