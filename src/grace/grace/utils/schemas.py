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
