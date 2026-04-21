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


# ── Enhanced Unconscious Layer ────────────────────────────────────────────────

@dataclass
class EmotionRegulationState:
    timestamp: float = field(default_factory=now)
    suppression: float = 0.2       # 0=none  1=exclusive use (expressive suppression)
    reappraisal: float = 0.5       # 0=none  1=exclusive use (cognitive reappraisal)
    rumination: float = 0.1        # 0=none  1=exclusive use (passive repetitive focus)
    acceptance: float = 0.2        # 0=none  1=exclusive use (acceptance/mindfulness)
    net_emotional_impact: float = 0.0  # Negative=harmful, Positive=beneficial
    strategy_entropy: float = 0.0  # Diversity of strategy use (higher=more adaptive)


@dataclass
class DisgustState:
    timestamp: float = field(default_factory=now)
    core_disgust: float = 0.2      # 0=none  1=high (bodily contaminants)
    animal_reminder_disgust: float = 0.1  # 0=none  1=high (animal nature reminders)
    moral_disgust: float = 0.3     # 0=none  1=high (moral violations)
    purity_concern: float = 0.4    # 0=none  1=high (purity/sanctity concerns)
    contamination_sensitivity: float = 0.5  # 0=low  1=high sensitivity
    overall_disgust: float = 0.0   # Combined disgust level (0-1)


@dataclass
class ConfabulationState:
    timestamp: float = field(default_factory=now)
    narrative: str = ""            # Generated narrative/explanation
    confidence: float = 0.5        # 0=no confidence  1=high confidence
    gap_severity_prior: float = 0.0  # Severity of gap that triggered confabulation
    is_confabulation: bool = False # True if this is a confabulated narrative
    sources_used: list = field(default_factory=list)  # Recent gap sources used


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


# ── Expanded Subconscious Layer ───────────────────────────────────────────────

@dataclass
class FutureSelfState:
    timestamp: float = field(default_factory=now)
    prospective_memory_count: int = 0        # Number of active prospective memories
    anticipatory_emotion: float = 0.0        # -1=negative  0=neutral  1=positive
    optimism_bias: float = 0.6               # Tendency to overestimate positive outcomes
    pessimism_bias: float = 0.3              # Tendency to underestimate negative outcomes
    upcoming_events: list = field(default_factory=list)  # Near-future events
    simulation_horizon: float = 86400.0      # Seconds ahead we simulate (default 1 day)


@dataclass
class SocialMirrorState:
    timestamp: float = field(default_factory=now)
    looking_glass_self: float = 0.5          # 0=others see us negatively  1=positively
    actual_social_feedback: float = 0.5      # 0=negative feedback  1=positive feedback
    self_esteem: float = 0.5                 # 0=low self-esteem  1=high self-esteem
    sociometer_reading: float = 0.5          # 0=excluded  0.5=neutral  1=included
    identity_coherence: float = 0.7          # 0=incoherent  1=coherent identity
    self_verification_motive: float = 0.6    # 0=no motive  1=strong drive to verify self-views
    congruence: float = 0.0                  # 0=no match  1=perfect match between LGS and actual feedback


@dataclass
class TheoryOfMindState:
    timestamp: float = field(default_factory=now)
    tom_level: int = 0                       # 0=none, 1=first order, 2=second order, etc.
    tom_accuracy: float = 0.6                # 0=no accuracy  1=perfect accuracy
    cognitive_load: float = 0.0              # 0=load  1=maximum load
    social_relevance: float = 0.0            # 0=not relevant  1=highly relevant
    cognitive_resources: float = 0.5         # 0=no resources  1=full resources
    executive_endorsement: float = 0.0       # 0=no endorsement  1=full endorsement
    available_resources: float = 0.5         # 0=no resources  1=full resources


@dataclass
class CounterfactualEmotionState:
    timestamp: float = field(default_factory=now)
    regret: float = 0.2                      # 0=no regret  1=intense regret
    relief: float = 0.3                      # 0=no relief  1=intense relief
    envy: float = 0.1                        # 0=no envy  1=intense envy
    gratitude: float = 0.4                   # 0=no gratitude  1=intense gratitude
    emotional_valence: float = 0.0           # -1=negative  0=neutral  1=positive
    complexity_score: float = 0.0            # 0=simple  1=complex emotional mix


# ── Affective Working Memory ─────────────────────────────────────────────────────

@dataclass
class AffectiveWorkingMemoryState:
    timestamp: float = field(default_factory=now)
    current_mood: float = 0.5                # -1=negative  0=neutral  1=positive
    mood_stability: float = 0.7              # 0=unstable  1=stable
    emotional_inertia: float = 0.3           # 0=fluid  1=rigid (resistance to change)
    mood_congruent_bias: float = 0.2         # Tendency to recall mood-congruent memories
    affective_capacity: float = 0.6          # Current affective processing load (0-1)
    dominant_emotion: str = "neutral"        # Currently dominant emotion label
    emotion_variability: float = 0.4         # 0=stable  1=highly variable
    stress_buffer: float = 0.5               # 0=no buffer  1=high buffering capacity


# ── Curiosity Gradient ────────────────────────────────────────────────────────

@dataclass
class CuriosityGradientState:
    timestamp: float = field(default_factory=now)
    information_gap: float = 0.5             # 0=no gap  1=maximum information gap
    curiosity_intensity: float = 0.6         # 0=no curiosity  1=burning curiosity
    novelty_sensitivity: float = 0.5         # 0=insensitive  1=highly sensitive to novelty
    knowledge_confidence: float = 0.7        # 0=no confidence  1=complete confidence in knowledge
    exploration_drive: float = 0.4           # 0=no drive  1=strong drive to explore
    information_novelty: float = 0.3         # 0=familiar  1=completely novel
    learning_progress: float = 0.5           # 0=no progress  1=rapid learning
    boredom_threshold: float = 0.6           # Threshold below which boredom occurs


# ── Social Comparison Engine ────────────────────────────────────────────────

@dataclass
class SocialComparisonState:
    timestamp: float = field(default_factory=now)
    comparison_direction: float = 0.0        # -1=worse than others  0=same  1=better than others
    comparison_importance: float = 0.5       # 0=not important  1=extremely important
    social_ranking: float = 0.5              # 0=lowest rank  1=highest rank in group
    envy_level: float = 0.1                  # 0=no envy  1=intense envy
    pride_level: float = 0.6                 # 0=no pride  1=excessive pride
    schadenfreude: float = 0.05              # 0=no schadenfreude  1=high schadenfreude
    competitiveness: float = 0.4             # 0=non-competitive  1=highly competitive
    conformity_pressure: float = 0.3         # 0=no pressure  1=high pressure to conform
    authenticity: float = 0.7                # 0=inauthentic  1=completely authentic


# ── Moral Disgust Memory ────────────────────────────────────────────────

@dataclass
class MoralDisgustMemoryState:
    timestamp: float = field(default_factory=now)
    contamination_sensitivity: float = 0.5   # 0=low sensitivity  1=high sensitivity to moral contamination
    contamination_history: float = 0.3       # 0=no history  1=extensive contamination history
    purification_motivation: float = 0.4     # 0=no motivation  1=strong motivation to purify
    moral_purity_ideal: float = 0.7          # 0=low standards  1=high moral purity standards
    contamination_avoidance: float = 0.6     # 0=no avoidance  1=strong avoidance of contaminants
    guilt_response: float = 0.2              # 0=no guilt  1=strong guilt response
    shame_response: float = 0.3              # 0=no shame  1=strong shame response
    restitution_drive: float = 0.5           # 0=no restitution  1=strong drive to make restitution
    forgiveness_capacity: float = 0.6        # 0=no forgiveness  1=high capacity for forgiveness


# ── Aesthetic Sensitivity System ────────────────────────────────────────

@dataclass
class AestheticSensitivityState:
    timestamp: float = field(default_factory=now)
    beauty_sensitivity: float = 0.6          # 0=insensitive  1=highly sensitive to beauty
    harmony_appreciation: float = 0.5        # 0=no appreciation  1=deep appreciation of harmony
    sublime_responsiveness: float = 0.3      # 0=unresponsive  1=highly responsive to sublime
    aesthetic_judgment_confidence: float = 0.4 # 0=no confidence  1=high confidence in aesthetic judgments
    novelty_seeking: float = 0.5             # 0=traditional  1=seeks novel aesthetic experiences
    emotional_resonance: float = 0.5         # 0=no resonance  1=deep emotional resonance with art
    cultural_openness: float = 0.5           # 0=ethnocentric  1=open to diverse aesthetic traditions
    aesthetic_memory: float = 0.4            # 0=poor recall  1=rich aesthetic memory
    creative_inspiration: float = 0.5        # 0=inspired  1=highly inspired by aesthetic experiences


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
