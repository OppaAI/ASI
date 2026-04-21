#!/usr/bin/env python3
"""
talk_to_grace.py  —  Full-brain conversational interface
Only YOU and GRACE appear in the chat.
Everything else (emotions, thoughts, memory, conscience, nodes) is in the fixed panel.

Layout:
  Row 1   ❤ emotion  valence  arousal  salience  meta  error  reward  ⚖ verdict  nodes
  Row 2   💭 inner monologue
  Row 3   ∴  symbolic conclusion
  Row 4   🧠 global workspace
  Row 5   👁 qualia
  Row 6   🗄 memory context  epi× sem×
  Row 7   📋 executive plan
  Row 8   🌙 default mode / dream / dissonance
  Row 9   📊 UNC:x/10  SUB:x/5  CON:x/11  CSC:x/3  QUA:x/1  DRM:x/4
  Row 10  ──────────────────────────────────────────────────────────────
  Row 11+ [scrolling] only You and GRACE
"""
import json
import shutil
import sys
import threading
import time

try:
    import rclpy
    from rclpy.node import Node
    from std_msgs.msg import String
except ImportError:
    print(
        "ERROR: ROS2 Python packages are not available.\n"
        "talk_to_grace.py requires ROS2 Humble (rclpy + std_msgs).\n\n"
        "Try:\n"
        "  source /opt/ros/humble/setup.bash\n"
        "  source ~/ros2_ws/install/setup.bash\n"
        "  python3 talk_to_grace.py\n"
    )
    sys.exit(1)

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

mv   = lambda r, c=1: f"\033[{r};{c}H"
clr  = lambda:        "\033[2K"
sav  = lambda:        "\033[s"
res  = lambda:        "\033[u"
hcur = lambda:        "\033[?25l"
scur = lambda:        "\033[?25h"
cls  = lambda:        "\033[2J"
scrl = lambda t, b:   f"\033[{t};{b}r"

PANEL = 10


def bar(val, width=7, color=GREEN):
    filled = int(max(0.0, min(1.0, float(val))) * width)
    return f"{color}{'█'*filled}{'░'*(width-filled)}{RESET}"


def trunc(s, n):
    s = str(s) if s else "..."
    return (s[:n-1] + "…") if len(s) > n else s


class GraceChat(Node):
    def __init__(self):
        super().__init__("grace_chat")

        # Publishers
        self._pub_audio  = self.create_publisher(String, "/grace/audio/in",                10)
        self._pub_bundle = self.create_publisher(String, "/grace/sensors/bundle",           10)
        self._pub_wm     = self.create_publisher(String, "/grace/conscious/working_memory", 10)
        self._pub_dream  = self.create_publisher(String, "/grace/dreaming/trigger",         10)

        # ── Brain state ───────────────────────────────────────────────────────
        self._emotion       = "serene"
        self._valence       = 0.6
        self._arousal       = 0.3
        self._salience      = 0.0
        self._reward        = 0.0
        self._pred_error    = 0.0
        self._meta_conf     = 0.0
        self._dissonance    = 0.0
        self._precision     = 0.75

        self._monologue     = "..."
        self._conclusion    = ""
        self._broadcast     = "..."
        self._qualia        = "..."
        self._unity         = 0.0
        self._ineffable     = False
        self._memory_ctx    = "..."
        self._epi_recalled  = ""
        self._sem_recalled  = ""
        self._proc_skills   = ""
        self._social        = ""
        self._epi_count     = 0
        self._sem_count     = 0

        self._plan          = ""
        self._plan_action   = ""
        self._plan_priority = 0.0
        self._wm_thought    = ""
        self._dmn           = ""
        self._identity      = ""

        self._verdict       = "neutral"
        self._verdict_conf  = 0.0
        self._blocked       = False
        self._moral_risk    = 0.0
        self._verse         = ""

        self._dream_tone    = ""
        self._imagination   = 0.0
        self._insights      = 0

        self._fired = {n: 0 for n in [
            "sensor_hub",
            "predictive_processing","prediction_error","thalamic_gate",
            "affective_core","reward_motivation","implicit_memory",
            "relevance_system","personality_core","preferences_values","hyper_model",
            "episodic_memory","semantic_memory","procedural_memory",
            "social_cognition","attitudes",
            "moral_knowledge","moral_reasoning","conscience_core",
            "qualia_binding",
            "working_memory","memory_coordinator","global_workspace",
            "reflection","metacognition","central_executive","salience_network",
            "default_mode","narrative_self","action_execution","conversation",
            "dreaming_process","imagination","distillation","consolidation",
        ]}

        self._last_speech   = ""
        self._waiting       = False

        # FIX: single lock guards ALL shared state — panel redraws AND chat prints
        self._lock          = threading.Lock()
        # Pending panel redraw flag — coalesce rapid updates into one draw
        self._needs_redraw  = False

        # Subscriptions
        subs = [
            ("/grace/unconscious/affective_state",      self._on_affect),
            ("/grace/unconscious/reward",               self._on_reward),
            ("/grace/unconscious/relevance",            self._on_relevance),
            ("/grace/unconscious/prediction_errors",    self._on_pred),
            ("/grace/unconscious/thalamic_broadcast",   self._on_thalamic),
            ("/grace/unconscious/personality",          self._on_personality),
            ("/grace/unconscious/values",               self._on_values),
            ("/grace/unconscious/precision",            self._on_precision),
            ("/grace/subconscious/episodic_recall",     self._on_episodic),
            ("/grace/subconscious/semantic_recall",     self._on_semantic),
            ("/grace/subconscious/procedural_recall",   self._on_procedural),
            ("/grace/subconscious/social_recall",       self._on_social),
            ("/grace/subconscious/attitudes",           self._on_attitudes),
            ("/grace/conscious/global_workspace",       self._on_gw),
            ("/grace/conscious/salience",               self._on_salience),
            ("/grace/conscious/reflection",             self._on_reflection),
            ("/grace/conscious/metacognition",          self._on_meta),
            ("/grace/conscious/executive_plan",         self._on_plan),
            ("/grace/conscious/memory_context",         self._on_memory),
            ("/grace/conscious/working_memory",         self._on_wm),
            ("/grace/conscious/dmn",                    self._on_dmn),
            ("/grace/conscious/narrative_self",         self._on_narrative),
            ("/grace/conscience/situation",             self._on_situation),
            ("/grace/conscience/reasoning",             self._on_reasoning),
            ("/grace/conscience/verdict",               self._on_verdict),
            ("/grace/qualia/field",                     self._on_qualia),
            ("/grace/dreaming/dream_content",           self._on_dream),
            ("/grace/dreaming/imagination",             self._on_imagination),
            ("/grace/dreaming/distillation",            self._on_distillation),
            ("/grace/dreaming/consolidation",           self._on_consolidation),
            ("/grace/speech/out",                       self._on_speech),
            ("/grace/action/log",                       self._on_action),
        ]
        for topic, cb in subs:
            self.create_subscription(String, topic, cb, 10)

        # Periodic panel refresh — runs on spin thread, rate-limited
        self.create_timer(0.25, self._maybe_redraw)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _mark_dirty(self):
        """Signal that the panel needs a redraw on the next timer tick."""
        self._needs_redraw = True

    def _maybe_redraw(self):
        """Called every 250ms on the spin thread. Only draws if something changed."""
        if self._needs_redraw:
            self._needs_redraw = False
            self._redraw()

    # ── Unconscious ───────────────────────────────────────────────────────────

    def _on_affect(self, msg):
        try:
            d = json.loads(msg.data)
            with self._lock:
                self._emotion    = d.get("emotion_label", self._emotion)
                self._valence    = d.get("valence",  self._valence)
                self._arousal    = d.get("arousal",  self._arousal)
                self._fired["affective_core"] += 1
            self._mark_dirty()
        except Exception: pass

    def _on_reward(self, msg):
        try:
            d = json.loads(msg.data)
            with self._lock:
                self._reward = d.get("value", 0.0)
                self._fired["reward_motivation"] += 1
            self._mark_dirty()
        except Exception: pass

    def _on_relevance(self, msg):
        try:
            d = json.loads(msg.data)
            with self._lock:
                # FIX: don't accumulate salience with max() forever —
                # blend toward new value so it can decay between turns
                new_score = d.get("score", 0.0)
                self._salience = self._salience * 0.7 + new_score * 0.3
                self._fired["relevance_system"] += 1
        except Exception: pass

    def _on_pred(self, msg):
        try:
            d = json.loads(msg.data)
            with self._lock:
                self._pred_error = d.get("error_magnitude", 0.0)
                self._fired["predictive_processing"] += 1
                self._fired["prediction_error"] += 1
        except Exception: pass

    def _on_thalamic(self, msg):
        try:
            with self._lock:
                self._fired["thalamic_gate"] += 1
        except Exception: pass

    def _on_personality(self, msg):
        try:
            with self._lock:
                self._fired["personality_core"] += 1
        except Exception: pass

    def _on_values(self, msg):
        try:
            with self._lock:
                self._fired["preferences_values"] += 1
        except Exception: pass

    def _on_precision(self, msg):
        try:
            d = json.loads(msg.data)
            with self._lock:
                self._precision = d.get("global_confidence", self._precision)
                self._fired["hyper_model"] += 1
        except Exception: pass

    # ── Subconscious ──────────────────────────────────────────────────────────

    def _on_episodic(self, msg):
        try:
            d = json.loads(msg.data)
            recalled = d.get("recalled", [])
            if recalled:
                first = recalled[0]
                c = first.get("content", str(first)) if isinstance(first, dict) else str(first)
                with self._lock:
                    self._epi_recalled = c[:70]
                    self._epi_count   += 1
                    self._fired["episodic_memory"] += 1
                self._mark_dirty()
        except Exception: pass

    def _on_semantic(self, msg):
        try:
            d = json.loads(msg.data)
            recalled = d.get("recalled", [])
            if recalled:
                first = recalled[0]
                c = first.get("content", str(first)) if isinstance(first, dict) else str(first)
                with self._lock:
                    self._sem_recalled = c[:70]
                    self._sem_count   += 1
                    self._fired["semantic_memory"] += 1
                self._mark_dirty()
        except Exception: pass

    def _on_procedural(self, msg):
        try:
            d = json.loads(msg.data)
            skills = d.get("skills", [])
            if skills:
                with self._lock:
                    self._proc_skills = ", ".join(
                        s.get("skill","?") for s in skills[:3])
                    self._fired["procedural_memory"] += 1
        except Exception: pass

    def _on_social(self, msg):
        try:
            d = json.loads(msg.data)
            gd = d.get("group_dynamic", "")
            if gd:
                with self._lock:
                    self._social = gd
                    self._fired["social_cognition"] += 1
        except Exception: pass

    def _on_attitudes(self, msg):
        try:
            d = json.loads(msg.data)
            with self._lock:
                self._dissonance = d.get("dissonance_level", 0.0)
                self._fired["attitudes"] += 1
        except Exception: pass

    # ── Conscious ─────────────────────────────────────────────────────────────

    def _on_gw(self, msg):
        try:
            d = json.loads(msg.data)
            bc = d.get("broadcast", "")
            if bc:
                with self._lock:
                    self._broadcast = bc
                    sal = d.get("salience", 0.0)
                    self._salience  = self._salience * 0.7 + sal * 0.3
                    self._fired["global_workspace"] += 1
                self._mark_dirty()
        except Exception: pass

    def _on_salience(self, msg):
        try:
            d = json.loads(msg.data)
            with self._lock:
                sal = d.get("salience", 0.0)
                self._salience = self._salience * 0.7 + sal * 0.3
                self._fired["salience_network"] += 1
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
                    self._fired["reflection"] += 1
                self._mark_dirty()
        except Exception: pass

    def _on_meta(self, msg):
        try:
            d = json.loads(msg.data)
            with self._lock:
                self._meta_conf = d.get("confidence_in_own_reasoning", self._meta_conf)
                self._fired["metacognition"] += 1
            self._mark_dirty()
        except Exception: pass

    def _on_plan(self, msg):
        try:
            d = json.loads(msg.data)
            goal  = d.get("goal", "")
            steps = d.get("steps", [])
            act   = steps[0].get("action","") if steps else ""
            prio  = d.get("priority", 0.0)
            if goal:
                with self._lock:
                    self._plan          = goal[:55]
                    self._plan_action   = act
                    self._plan_priority = prio
                    self._fired["central_executive"] += 1
                self._mark_dirty()
        except Exception: pass

    def _on_memory(self, msg):
        try:
            d = json.loads(msg.data)
            bc = d.get("broadcast", "")
            if bc:
                with self._lock:
                    self._memory_ctx = bc
                    self._fired["memory_coordinator"] += 1
                self._mark_dirty()
        except Exception: pass

    def _on_wm(self, msg):
        try:
            d = json.loads(msg.data)
            t = d.get("active_thought","")
            with self._lock:
                self._wm_thought = t
                self._fired["working_memory"] += 1
        except Exception: pass

    def _on_dmn(self, msg):
        try:
            d = json.loads(msg.data)
            sim = d.get("narrative_simulation","")
            if sim:
                with self._lock:
                    self._dmn = sim[:70]
                    self._fired["default_mode"] += 1
                self._mark_dirty()
        except Exception: pass

    def _on_narrative(self, msg):
        try:
            d = json.loads(msg.data)
            ident = d.get("identity_summary","")
            if ident:
                with self._lock:
                    self._identity = ident[:60]
                    self._fired["narrative_self"] += 1
        except Exception: pass

    # ── Conscience ────────────────────────────────────────────────────────────

    def _on_situation(self, msg):
        try:
            with self._lock:
                self._fired["conscience_core"] += 1
        except Exception: pass

    def _on_reasoning(self, msg):
        try:
            d = json.loads(msg.data)
            with self._lock:
                self._moral_risk = d.get("overall_moral_risk", 0.0)
                self._fired["moral_reasoning"] += 1
            self._mark_dirty()
        except Exception: pass

    def _on_verdict(self, msg):
        try:
            d = json.loads(msg.data)
            with self._lock:
                self._verdict      = d.get("verdict",      "neutral")
                self._verdict_conf = d.get("confidence",   0.0)
                self._blocked      = d.get("block_action", False)
                self._verse        = d.get("verse_reference","")
                self._fired["conscience_core"] += 1
            self._mark_dirty()
        except Exception: pass

    # ── Qualia ────────────────────────────────────────────────────────────────

    def _on_qualia(self, msg):
        try:
            d = json.loads(msg.data)
            pc = d.get("phenomenal_content","")
            if pc:
                with self._lock:
                    self._qualia    = pc[:80]
                    self._unity     = d.get("unity_score", 0.0)
                    self._ineffable = d.get("ineffability_flag", False)
                    self._fired["qualia_binding"] += 1
                self._mark_dirty()
        except Exception: pass

    # ── Dreaming ──────────────────────────────────────────────────────────────

    def _on_dream(self, msg):
        try:
            d = json.loads(msg.data)
            tone = d.get("emotional_tone","")
            if tone:
                with self._lock:
                    self._dream_tone = tone
                    self._fired["dreaming_process"] += 1
                self._mark_dirty()
        except Exception: pass

    def _on_imagination(self, msg):
        try:
            d = json.loads(msg.data)
            with self._lock:
                self._imagination = d.get("novelty_score", 0.0)
                self._fired["imagination"] += 1
            self._mark_dirty()
        except Exception: pass

    def _on_distillation(self, msg):
        try:
            d = json.loads(msg.data)
            with self._lock:
                self._insights += len(d.get("insights",[]))
                self._fired["distillation"] += 1
        except Exception: pass

    def _on_consolidation(self, msg):
        try:
            with self._lock:
                self._fired["consolidation"] += 1
            self._mark_dirty()
        except Exception: pass

    # ── Output — ONLY speech goes to the chat area ────────────────────────────

    def _on_speech(self, msg):
        text = msg.data.strip()
        if text and text != self._last_speech:
            self._last_speech = text
            with self._lock:
                self._fired["conversation"] += 1
            # _chat acquires the lock internally — don't hold it here
            self._chat(f"\n{GREEN}{BOLD}GRACE:{RESET} {GREEN}{text}{RESET}\n")
            self._waiting = False

    def _on_action(self, msg):
        try:
            with self._lock:
                self._fired["action_execution"] += 1
        except Exception: pass

    # ── Panel ─────────────────────────────────────────────────────────────────

    def _redraw(self):
        """
        Render the fixed-position brain-state panel (rows 1-10).
        Must only be called from the spin thread (via _maybe_redraw timer)
        or while holding self._lock from the main thread.
        """
        w = shutil.get_terminal_size((110, 30)).columns

        with self._lock:
            emotion       = self._emotion
            valence       = self._valence
            arousal       = self._arousal
            salience      = self._salience
            meta_conf     = self._meta_conf
            pred_error    = self._pred_error
            reward        = self._reward
            verdict       = self._verdict
            verdict_conf  = self._verdict_conf
            blocked       = self._blocked
            monologue     = self._monologue
            conclusion    = self._conclusion
            wm_thought    = self._wm_thought
            broadcast     = self._broadcast
            qualia        = self._qualia
            unity         = self._unity
            ineffable     = self._ineffable
            memory_ctx    = self._memory_ctx
            epi_count     = self._epi_count
            sem_count     = self._sem_count
            plan          = self._plan
            plan_action   = self._plan_action
            plan_priority = self._plan_priority
            dmn           = self._dmn
            dream_tone    = self._dream_tone
            imagination   = self._imagination
            dissonance    = self._dissonance
            insights      = self._insights
            fired         = dict(self._fired)

        layers = [
            ("UNC", ["affective_core","reward_motivation","predictive_processing",
                     "prediction_error","thalamic_gate","relevance_system",
                     "implicit_memory","personality_core","preferences_values","hyper_model"]),
            ("SUB", ["episodic_memory","semantic_memory","procedural_memory",
                     "social_cognition","attitudes"]),
            ("CON", ["global_workspace","working_memory","salience_network",
                     "reflection","metacognition","central_executive",
                     "memory_coordinator","default_mode","narrative_self",
                     "action_execution","conversation"]),
            ("CSC", ["moral_knowledge","moral_reasoning","conscience_core"]),
            ("QUA", ["qualia_binding"]),
            ("DRM", ["dreaming_process","imagination","distillation","consolidation"]),
        ]

        active_nodes = sum(1 for v in fired.values() if v > 0)
        total_nodes  = len(fired)

        vc = (RED    if verdict == "immoral"   else
              GREEN  if verdict == "moral"     else
              YELLOW if verdict == "uncertain" else DIM)

        out = sav()

        # Row 1 — vital signs
        out += mv(1); out += clr()
        out += f"{CYAN}{BOLD} GRACE {RESET}"
        out += f" ❤{bar(valence,6,MAGENTA)}"
        out += f" ⚡{bar(arousal,6,YELLOW)}"
        out += f" 🎯{bar(salience,6,CYAN)}"
        out += f" {MAGENTA}{BOLD}{emotion:<11}{RESET}"
        out += f" {DIM}meta:{GREEN}{meta_conf:.2f}{RESET}"
        out += f" {DIM}err:{YELLOW}{pred_error:.2f}{RESET}"
        out += f" {DIM}rew:{GREEN if reward>=0 else RED}{reward:+.2f}{RESET}"
        out += f" {vc}⚖{verdict}({verdict_conf:.2f}){RESET}"
        out += f" {DIM}🔵{GREEN}{active_nodes}{DIM}/{total_nodes}{RESET}"

        # Row 2 — inner monologue
        out += mv(2); out += clr()
        out += f"{DIM} 💭 {MAGENTA}{trunc(monologue, w-6)}{RESET}"

        # Row 3 — symbolic conclusion / active thought
        out += mv(3); out += clr()
        conc = conclusion or wm_thought or "..."
        out += f"{DIM} ∴  {WHITE}{trunc(conc, w-6)}{RESET}"

        # Row 4 — global workspace
        out += mv(4); out += clr()
        out += f"{DIM} 🧠 {WHITE}{trunc(broadcast, w-6)}{RESET}"

        # Row 5 — qualia
        out += mv(5); out += clr()
        unity_s = f" Φ={unity:.2f}" if unity > 0 else ""
        ineff_s = " ✦" if ineffable else ""
        out += f"{DIM} 👁  {MAGENTA}{trunc(qualia, w-18)}{DIM}{unity_s}{ineff_s}{RESET}"

        # Row 6 — memory context + recall counts
        out += mv(6); out += clr()
        mem_right = f"  {DIM}epi×{epi_count} sem×{sem_count}{RESET}"
        mem_w = w - 6 - len(f"  epi×{epi_count} sem×{sem_count}")
        out += f"{DIM} 🗄  {CYAN}{trunc(memory_ctx, mem_w)}{RESET}{mem_right}"

        # Row 7 — executive plan
        out += mv(7); out += clr()
        plan_s = f"[{plan_action}] {plan}" if plan_action else plan or "..."
        prio_s = f" p={plan_priority:.2f}" if plan_priority > 0 else ""
        out += f"{DIM} 📋 {GREEN}{trunc(plan_s, w-12)}{DIM}{prio_s}{RESET}"

        # Row 8 — default mode / dream / dissonance
        out += mv(8); out += clr()
        dmn_s   = trunc(dmn, 45) if dmn else "idle"
        parts   = [f"dmn:{BLUE}{dmn_s}{RESET}"]
        if dream_tone:   parts.append(f"{DIM}dream:{dream_tone}{RESET}")
        if imagination:  parts.append(f"{DIM}novelty:{imagination:.2f}{RESET}")
        if dissonance:   parts.append(f"{DIM}dissonance:{dissonance:.2f}{RESET}")
        if insights:     parts.append(f"{DIM}insights:{insights}{RESET}")
        out += f"{DIM} 🌙 {RESET}" + "  ".join(parts)

        # Row 9 — node layer activity
        out += mv(9); out += clr()
        row9 = f" 📊 "
        for label, nodes in layers:
            total = len(nodes)
            active_in_layer = sum(1 for n in nodes if fired.get(n,0) > 0)
            calls = sum(fired.get(n,0) for n in nodes)
            color = GREEN if active_in_layer==total else (YELLOW if active_in_layer>0 else RED)
            row9 += f"{DIM}{label}:{color}{active_in_layer}/{total}{DIM}×{calls}  {RESET}"
        out += row9

        # Row 10 — separator
        out += mv(10); out += clr()
        out += f"{DIM}{'─'*w}{RESET}"

        out += res()
        print(out, end="", flush=True)

    # ── Chat — only You and GRACE ────────────────────────────────────────────

    def _chat(self, text):
        """
        Print a line into the scrolling chat region (below row 10).
        Acquires lock to prevent interleaving with _redraw().
        """
        with self._lock:
            print(text, flush=True)

    # ── Send ──────────────────────────────────────────────────────────────────

    def send(self, text: str):
        a = String(); a.data = text
        self._pub_audio.publish(a)

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

        wm = {
            "timestamp":      time.time(),
            "active_thought": text,
            "phonological":   [text[:80]],
            "visuospatial":   [],
        }
        w = String(); w.data = json.dumps(wm)
        self._pub_wm.publish(w)

        with self._lock:
            self._fired["sensor_hub"] += 1
            # FIX: reset salience on new turn so it doesn't stay pinned
            self._salience = 0.0

        self._waiting = True


def spin_thread(node):
    rclpy.spin(node)


def main():
    rclpy.init()
    node = GraceChat()

    t = threading.Thread(target=spin_thread, args=(node,), daemon=True)
    t.start()

    rows = shutil.get_terminal_size((110, 30)).lines

    print(hcur(), end="")
    print(cls(),  end="")
    print(scrl(PANEL+1, rows), end="", flush=True)
    print(mv(PANEL+1), end="", flush=True)

    node._redraw()
    print(f"{DIM}  Connecting...{RESET}", flush=True)
    time.sleep(1.5)
    node._redraw()

    # FIX: increase LLM timeout to 60s for large models on Jetson
    LLM_TIMEOUT = 60.0

    try:
        while True:
            print(scur(), end="", flush=True)
            with node._lock:
                emotion = node._emotion
                blocked = node._blocked
            color   = RED if blocked else CYAN
            print(f"{color}{BOLD}You [{emotion}]:{RESET} ", end="", flush=True)

            try:
                user_input = input("").strip()
            except EOFError:
                break

            print(hcur(), end="", flush=True)

            if not user_input:
                continue
            if user_input.lower() in ("quit","exit","bye"):
                node._chat(f"\n{GREEN}GRACE: Goodbye.{RESET}\n")
                break

            # ── Commands ──────────────────────────────────────────────────────
            if user_input.lower() == "/dream":
                d = String(); d.data = "{}"
                node._pub_dream.publish(d)
                node._chat(f"{DIM}  🌙 Dream triggered{RESET}")
                continue

            if user_input.lower() == "/memory":
                with node._lock:
                    epi = node._epi_recalled or "—"
                    sem = node._sem_recalled or "—"
                    soc = node._social or "—"
                    ident = node._identity or "—"
                    ec = node._epi_count
                    sc = node._sem_count
                node._chat(
                    f"\n{CYAN}{BOLD}Memory snapshot:{RESET}\n"
                    f"  {DIM}Episodic (×{ec}): {epi}{RESET}\n"
                    f"  {DIM}Semantic (×{sc}): {sem}{RESET}\n"
                    f"  {DIM}Social: {soc}{RESET}\n"
                    f"  {DIM}Identity: {ident}{RESET}\n")
                continue

            if user_input.lower() == "/nodes":
                with node._lock:
                    fired_copy = dict(node._fired)
                lines = [f"\n{CYAN}{BOLD}Node activity:{RESET}"]
                for name, count in sorted(fired_copy.items(),
                                          key=lambda x: x[1], reverse=True):
                    c = GREEN if count > 0 else RED
                    lines.append(
                        f"  {c}{'●' if count>0 else '○'}{RESET} "
                        f"{DIM}{name:<30}×{count}{RESET}")
                lines.append("")
                node._chat("\n".join(lines))
                continue

            if user_input.lower() == "/help":
                node._chat(
                    f"\n{CYAN}{BOLD}Commands:{RESET}\n"
                    f"  {BOLD}/dream{RESET}   trigger dream cycle\n"
                    f"  {BOLD}/memory{RESET}  show memory recalls\n"
                    f"  {BOLD}/nodes{RESET}   show all 35 node counts\n"
                    f"  {BOLD}/help{RESET}    this list\n"
                    f"  {BOLD}quit{RESET}     exit\n")
                continue

            # ── Normal conversation ───────────────────────────────────────────
            node._chat(f"{CYAN}You [{emotion}]:{RESET} {user_input}")
            node.send(user_input)

            # FIX: longer timeout, poll more gently, no misleading "still thinking"
            deadline = time.time() + LLM_TIMEOUT
            while node._waiting and time.time() < deadline:
                time.sleep(0.15)

            if node._waiting:
                node._chat(f"{YELLOW}  ⌛ still processing... (reply will appear below){RESET}")
                node._waiting = False

    except KeyboardInterrupt:
        pass

    print(scur(), end="")
    print(scrl(1, rows), end="")
    print(cls(), end="", flush=True)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
