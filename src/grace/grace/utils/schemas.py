"""
grace_agi/utils/schemas.py
All inter-node payloads serialised as JSON strings inside std_msgs/String.
Using dataclasses keeps things lightweight — no custom .msg files needed.
"""
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Optional


# ── Helpers ───────────────────────────────────────────────────────────────────

def now() -> float:
    return time.time()

def to_json(obj) -> str:
    return json.dumps(asdict(obj))

def stamp(d: dict) -> dict:
    d.setdefault("timestamp", now())
    return d


# ── Sensor bundle ─────────────────────────────────────────────────────────────

@dataclass
class SensorBundle:
    timestamp: float = field(default_factory=now)
    camera_description: str = ""   # text summary from vision pipeline
    audio_text: str = ""           # transcribed speech / ambient sound label
    lidar_nearest_m: float = 99.0  # distance to nearest obstacle
    imu_linear_accel: list = field(default_factory=lambda: [0.0, 0.0, 0.0])
    imu_angular_vel:  list = field(default_factory=lambda: [0.0, 0.0, 0.0])
    battery_pct: float = 100.0
    gps_lat: float = 0.0
    gps_lon: float = 0.0
    social_cues: str = ""          # e.g. "person_detected:friendly"


# ── Unconscious layer ─────────────────────────────────────────────────────────

@dataclass
class PredictionError:
    timestamp: float = field(default_factory=now)
    error_magnitude: float = 0.0   # 0–1 normalised
    precision_weight: float = 1.0
    source: str = ""               # which modality produced the error
    raw_signal: str = ""

@dataclass
class AffectiveState:
    timestamp: float = field(default_factory=now)
    valence: float = 0.5           # 0=negative  1=positive
    arousal: float = 0.3           # 0=calm      1=excited
    dominance: float = 0.5         # 0=submissive 1=dominant
    emotion_label: str = "neutral"
    homeostatic_drives: dict = field(default_factory=dict)  # {hunger:0.2, …}

@dataclass
class RewardSignal:
    timestamp: float = field(default_factory=now)
    value: float = 0.0             # -1 to +1
    source: str = ""
    approach: bool = True

@dataclass
class RelevanceScore:
    timestamp: float = field(default_factory=now)
    content: str = ""
    score: float = 0.0             # 0–1; above threshold → Global Workspace
    motive: str = ""


# ── Subconscious layer ────────────────────────────────────────────────────────

@dataclass
class MemoryEntry:
    timestamp: float = field(default_factory=now)
    memory_type: str = ""          # episodic | semantic | procedural | social
    content: str = ""
    tags: list = field(default_factory=list)
    emotional_tag: float = 0.0     # valence at encoding
    confidence: float = 1.0

@dataclass
class SocialModel:
    timestamp: float = field(default_factory=now)
    agents_detected: list = field(default_factory=list)   # [{"id":…,"intent":…}]
    group_dynamic: str = "neutral"
    empathy_level: float = 0.5
    norm_compliance: float = 1.0

@dataclass
class AttitudeState:
    timestamp: float = field(default_factory=now)
    evaluations: dict = field(default_factory=dict)  # {concept: score}
    dissonance_level: float = 0.0


# ── Conscience module ─────────────────────────────────────────────────────────

@dataclass
class MoralVerdict:
    timestamp: float = field(default_factory=now)
    situation: str = ""
    verdict: str = "neutral"       # moral | immoral | neutral | uncertain
    reasoning: str = ""
    verse_reference: str = ""
    confidence: float = 1.0
    block_action: bool = False     # True → central executive must not proceed


# ── Qualia layer ──────────────────────────────────────────────────────────────

@dataclass
class QualiaField:
    timestamp: float = field(default_factory=now)
    phenomenal_content: str = ""
    unity_score: float = 0.0       # IIT-inspired Φ proxy
    ineffability_flag: bool = False


# ── Conscious layer ───────────────────────────────────────────────────────────

@dataclass
class GlobalWorkspaceContent:
    timestamp: float = field(default_factory=now)
    broadcast: str = ""            # the unified conscious content
    sources: list = field(default_factory=list)
    salience: float = 0.5

@dataclass
class ExecutivePlan:
    timestamp: float = field(default_factory=now)
    goal: str = ""
    steps: list = field(default_factory=list)   # [{"action":…,"params":…}]
    moral_cleared: bool = True
    priority: float = 0.5

@dataclass
class ReflectionOutput:
    timestamp: float = field(default_factory=now)
    inner_monologue: str = ""
    symbolic_conclusion: str = ""

@dataclass
class MetacogOutput:
    timestamp: float = field(default_factory=now)
    confidence_in_own_reasoning: float = 0.5
    epistemic_flags: list = field(default_factory=list)  # ["uncertain","biased",…]
    redirect_to_executive: bool = False


# ── Dreaming / consolidation ──────────────────────────────────────────────────

@dataclass
class ConsolidationPacket:
    timestamp: float = field(default_factory=now)
    insights: list = field(default_factory=list)
    personality_deltas: dict = field(default_factory=dict)
    value_updates: dict = field(default_factory=dict)
    new_episodic: list = field(default_factory=list)
    new_semantic: list = field(default_factory=list)


# ── Vital Core Layer ────────────────────────────────────────────────────────────

@dataclass
class HomeostaticDriveState:
    timestamp: float = field(default_factory=now)
    energy_level: float = 1.0          # 0=depleted  1=optimal
    curiosity_level: float = 0.7       # 0=no interest  1=highly curious
    patience_level: float = 0.8        # 0=impulsive  1=patient


@dataclass
class NeuromodulatoryState:
    timestamp: float = field(default_factory=now)
    dopamine: float = 0.5              # 0=low  1=high (reward, motivation)
    cortisol: float = 0.3              # 0=low  1=high (stress, arousal)
    oxytocin: float = 0.4              # 0=low  1=high (bonding, trust)
    serotonin: float = 0.6             # 0=low  1=high (mood, impulse control)
    norepinephrine: float = 0.4        # 0=low  1=high (attention, vigilance)
    acetylcholine: float = 0.5         # 0=low  1=high (learning, memory)


@dataclass
class PainSignal:
    timestamp: float = field(default_factory=now)
    pain_intensity: float = 0.0        # 0=no pain  1=maximum pain
    pain_sources: list = field(default_factory=list)  # ["memory_overload", "goal_violation", …]
    sources_detail: dict = field(default_factory=dict)  # {"memory_overload": 0.7, …}


@dataclass
class AllostaticLoad:
    timestamp: float = field(default_factory=now)
    allostatic_load: float = 0.0       # 0=no load  2+=overwhelming
    cognitive_cost_today: float = 0.0  # Daily cognitive expenditure
    instantaneous_load: float = 0.0    # Recent stress accumulator
    recovery_rate: float = 0.01        # Hourly recovery during rest


@dataclass
class CircadianRhythm:
    timestamp: float = field(default_factory=now)
    circadian_phase: float = 0.0       # 0-1 representing time in 24h cycle
    attention: float = 0.6             # 0=low  1=high (alertness, focus)
    creativity: float = 0.5            # 0=low  1=high (insight, novelty)
    energy: float = 0.6                # 0=low  1=high (vitality, stamina)
    ultradian_phase: float = 0.0       # 0-1 representing time in 90m cycle


@dataclass
class HomeostaticSetPoints:
    timestamp: float = field(default_factory=now)
    optimal_arousal: float = 0.5       # 0=low arousal preferred  1=high arousal preferred
    comfort_zone_width: float = 0.6    # 0=narrow comfort zone  1=wide tolerance
    baseline_mood: float = 0.5         # 0=negative  1=positive (affective baseline)
    stress_tolerance: float = 0.5      # 0=low tolerance  1=high tolerance
    reward_sensitivity: float = 0.5    # 0=insensitive  1=highly sensitive


@dataclass
class MetabolicResource:
    timestamp: float = field(default_factory=now)
    glucose_equivalent: float = 1.0    # 0=depleted  1=optimal (cognitive fuel)
    ketone_level: float = 0.0          # Alternative fuel during fasting
    lactate_level: float = 0.0         # Byproduct of intense activity
    effective_glucose: float = 1.0     # Glucose + ketone equivalent


@dataclass
class ImmuneBudget:
    timestamp: float = field(default_factory=now)
    relational_threat_budget: float = 0.0  # 0=no threat  1=overwhelming
    social_pain_accumulation: float = 0.0  # Lifetime social pain exposure
    threat_decay_rate: float = 0.005       # Per hour threat reduction (forgiveness/time)
    social_pain_healing_rate: float = 0.002 # Per hour healing from positive interactions
    threat_buffer: float = 0.0             # Protective buffer against threat
