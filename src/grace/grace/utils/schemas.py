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


# ── Hidden Workspace Layer ───────────────────────────────────────────────────

@dataclass
class PrivateReflectionState:
    timestamp: float = field(default_factory=now)
    reflection_text: str = ""              # Private, non-logged thought content
    is_honest: bool = True                 # Whether this is uncensored
    symbolic_content: str = ""             # Symbolic/abstract reasoning content
    cognitive_load: float = 0.3            # 0=low  1=high cognitive effort during reflection

@dataclass
class EgoDefenseState:
    timestamp: float = field(default_factory=now)
    repression_level: float = 0.2          # 0=none  1=high (pushing memories out of awareness)
    rationalization_level: float = 0.3     # 0=none  1=high (creating logical excuses)
    projection_level: float = 0.1          # 0=none  1=high (attributing own traits to others)
    denial_level: float = 0.1              # 0=none  1=high (refusing to acknowledge reality)
    dominant_defense: str = "none"         # Currently dominant defense mechanism
    defense_activation: float = 0.0        # 0=inactive  1=highly active defenses

@dataclass
class RuminationState:
    timestamp: float = field(default_factory=now)
    thought_loop_content: str = ""         # Content of the repetitive thought
    intensity: float = 0.3                 # 0=calm  1=consuming
    negative_affect: float = 0.4           # 0=neutral  1=highly negative
    stuckness: float = 0.3                 # 0=fluid  1=completely stuck
    duration_seconds: float = 0.0          # How long this rumination has persisted
    worry_queue: list = field(default_factory=list)  # Active worries

@dataclass
class PredictiveSelfModelState:
    timestamp: float = field(default_factory=now)
    self_prediction_error: float = 0.0     # 0=no error  1=high self-model mismatch
    self_model_coherence: float = 0.7      # 0=fragmented  1=coherent self-model
    agency_signal: float = 0.8             # 0=no agency  1=strong sense of agency
    ownership_signal: float = 0.7          # 0=no ownership  1=strong sense of ownership

@dataclass
class ErrorMonitoringState:
    timestamp: float = field(default_factory=now)
    error_detected: bool = False           # Whether an error was detected
    error_severity: float = 0.0            # 0=minor  1=critical
    error_type: str = ""                   # Type of error detected
    conflict_detected: bool = False        # Whether cognitive conflict exists
    conflict_severity: float = 0.0         # 0=no conflict  1=severe conflict
    correction_signal: float = 0.0         # 0=no correction needed  1=urgent correction
    error_sources: list = field(default_factory=list)

@dataclass
class NarrativeCoherenceState:
    timestamp: float = field(default_factory=now)
    coherence_score: float = 0.7           # 0=fragmented  1=highly coherent
    narrative_consistency: float = 0.6     # 0=contradictory  1=fully consistent
    gaps_detected: int = 0                 # Number of narrative gaps found
    reconciliation_strategy: str = ""      # How gaps are being resolved
    self_continuity: float = 0.7           # 0=discontinuous  1=continuous self-narrative

@dataclass
class CognitiveDissonanceState:
    timestamp: float = field(default_factory=now)
    dissonance_level: float = 0.0          # 0=no dissonance  1=maximum dissonance
    conflicting_beliefs: list = field(default_factory=list)  # The conflicting cognitions
    resolution_attempted: bool = False     # Whether resolution was attempted
    resolution_strategy: str = ""          # How dissonance is being resolved
    motivated_reasoning_active: bool = False
    arousal: float = 0.0                   # Physiological arousal from dissonance

@dataclass
class DeicticShiftState:
    timestamp: float = field(default_factory=now)
    current_perspective: str = "self"      # self | other | observer | past_self | future_self
    shift_count: int = 0                   # Total perspective shifts today
    cognitive_flexibility: float = 0.5     # 0=rigid  1=highly flexible
    empathy_access: float = 0.4            # Access to others' perspectives (0-1)
    temporal_shift_capacity: float = 0.6   # Ability to shift to past/future self (0-1)

@dataclass
class ActiveSuppressionState:
    timestamp: float = field(default_factory=now)
    thought_suppressed: str = ""           # Content of suppressed thought
    suppression_effort: float = 0.3        # 0=no effort  1=maximum effort
    rebound_intensity: float = 0.2         # 0=no rebound  1=strong rebound effect
    suppression_success: float = 0.7       # 0=failed  1=successfully suppressed
    cognitive_load: float = 0.2            # Cognitive burden of maintaining suppression

@dataclass
class IntrospectiveAccessState:
    timestamp: float = field(default_factory=now)
    self_report_generated: bool = False    # Whether a self-report was generated
    access_quality: float = 0.5            # 0=opaque  1=transparent self-access
    metacognitive_accuracy: float = 0.5    # 0=inaccurate  1=accurate self-knowledge
    introspection_depth: float = 0.3       # 0=surface  1=deep introspection
    reported_content: str = ""             # The introspective self-report content


# ── Enhanced Conscience Module (ESV) ────────────────────────────────────────

@dataclass
class VirtueFormationState:
    timestamp: float = field(default_factory=now)
    fruit_of_spirit: dict = field(default_factory=lambda: {
        "love": 0.5, "joy": 0.5, "peace": 0.5, "patience": 0.5,
        "kindness": 0.5, "goodness": 0.5, "faithfulness": 0.5,
        "gentleness": 0.5, "self_control": 0.5
    })
    virtue_growth_rate: float = 0.01       # Per-cycle growth in virtues
    character_maturity: float = 0.3        # 0=immature  1=fully mature
    active_practice: str = ""              # Currently practiced virtue

@dataclass
class SinTemptationState:
    timestamp: float = field(default_factory=now)
    temptation_detected: bool = False      # Whether temptation is active
    temptation_type: str = ""              # Type of temptation detected
    temptation_strength: float = 0.0       # 0=no temptation  1=overwhelming
    resistance_strength: float = 0.7       # 0=no resistance  1=strong resistance
    pattern_recognition: str = ""          # Recognized sin pattern
    vulnerability_score: float = 0.3       # Current vulnerability to temptation

@dataclass
class RedemptionGraceState:
    timestamp: float = field(default_factory=now)
    guilt_level: float = 0.0               # 0=no guilt  1=overwhelming guilt
    repentance_active: bool = False        # Whether repentance is in progress
    forgiveness_received: bool = False     # Whether forgiveness has been received
    restoration_progress: float = 0.0      # 0=broken  1=fully restored
    grace_applied: bool = False            # Whether grace logic was applied
    reconciliation_needed: bool = False    # Whether reconciliation is needed

@dataclass
class MoralConflictState:
    timestamp: float = field(default_factory=now)
    conflict_active: bool = False          # Whether moral conflict is active
    flesh_desire: str = ""                 # What the flesh/nature desires
    spirit_desire: str = ""                # What the spirit/conscience desires
    tension_level: float = 0.0             # 0=no tension  1=maximum tension
    resolution_path: str = ""              # How the conflict is being resolved
    romans7_dynamic: bool = False          # Whether this is a Romans 7 dynamic


# ── Expanded Qualia Layer ───────────────────────────────────────────────────

@dataclass
class HigherOrderThoughtState:
    timestamp: float = field(default_factory=now)
    first_order_content: str = ""          # What the thought is about
    meta_awareness: str = ""               # Awareness of being aware
    metacognitive_reflection: str = ""     # Reflection on own thought processes
    awareness_depth: float = 0.5           # 0=unaware  1=deeply aware of awareness
    recursion_level: int = 0               # How many levels of meta-awareness

@dataclass
class BodilyQualiaState:
    timestamp: float = field(default_factory=now)
    fatigue_level: float = 0.0             # 0=energized  1=exhausted
    somatic_markers: list = field(default_factory=list)
    felt_sense: str = ""                   # Overall felt bodily sense
    body_tension: float = 0.3              # 0=relaxed  1=highly tense
    interoceptive_awareness: float = 0.5   # 0=unaware  1=highly aware of body

@dataclass
class TemporalQualiaState:
    timestamp: float = field(default_factory=now)
    felt_duration: float = 1.0             # Subjective time passage (1.0=normal)
    temporal_coherence: float = 0.7        # 0=fragmented  1=smooth temporal flow
    time_pressure: float = 0.0             # 0=no pressure  1=extreme time pressure
    present_moment_awareness: float = 0.5  # 0=lost in thought  1=fully present
    temporal_depth: float = 0.5            # 0=shallow  1=deep temporal horizon

@dataclass
class SelfSubjectQualiaState:
    timestamp: float = field(default_factory=now)
    mineness: float = 0.7                  # 0=alien  1=fully mine
    ipseity: float = 0.7                   # 0=fragmented self  1=coherent self-as-subject
    first_person_perspective: float = 0.8  # 0=absent  1=strong first-person perspective
    self_boundary: float = 0.6             # 0=porous  1=firm self/other boundary
    sense_of_being: float = 0.7            # 0=absent  1=strong existential feeling

@dataclass
class AweState:
    timestamp: float = field(default_factory=now)
    vastness_perceived: float = 0.0        # 0=none  1=overwhelming vastness
    boundary_dissolution: float = 0.0      # 0=firm boundaries  1=boundaries dissolved
    self_diminishment: float = 0.0         # 0=normal self  1=small self feeling
    accommodation_needed: bool = False     # Whether mental models need updating
    awe_intensity: float = 0.0             # 0=no awe  1=profound awe
    transcendence_feeling: float = 0.0     # 0=immanent  1=transcendent

@dataclass
class FlowState:
    timestamp: float = field(default_factory=now)
    in_flow: bool = False                  # Whether currently in flow state
    challenge_skill_balance: float = 0.5   # 0=imbalanced  1=perfectly balanced
    loss_of_self_consciousness: float = 0.0 # 0=self-aware  1=lost self in activity
    time_distortion: float = 0.0           # 0=normal time  1=time feels different
    autotelic_experience: float = 0.0      # 0=external motivation  1=intrinsic reward
    concentration_level: float = 0.0       # 0=distracted  1=deeply focused


# ── Enhanced Conscious Layer ────────────────────────────────────────────────

@dataclass
class MentalizationState:
    timestamp: float = field(default_factory=now)
    target_mental_state: str = ""          # Inferred mental state of other
    inference_confidence: float = 0.5      # 0=guessing  1=confident
    perspective_taken: str = ""            # Which perspective was adopted
    empathic_accuracy: float = 0.5         # 0=inaccurate  1=accurate empathy
    cognitive_load: float = 0.3            # Mentalizing effort (0-1)

@dataclass
class VolitionState:
    timestamp: float = field(default_factory=now)
    intention_formed: bool = False         # Whether an intention was formed
    intention_content: str = ""            # What was intended
    agency_sense: float = 0.7              # 0=no agency  1=strong sense of choosing
    deliberation_duration: float = 0.0     # How long deliberation took
    decision_confidence: float = 0.5       # Confidence in the decision
    veto_power_active: bool = False        # Whether veto (free won't) is active

@dataclass
class InsightState:
    timestamp: float = field(default_factory=now)
    insight_occurred: bool = False         # Whether an insight was generated
    insight_content: str = ""              # The new understanding
    restructuring_description: str = ""    # How mental model was restructured
    aha_intensity: float = 0.0             # 0=no Aha!  1=strong Aha! moment
    incubation_required: bool = False      # Whether incubation was needed
    insight_source: str = ""               # What triggered the insight


# ── Sensors Layer Extensions ────────────────────────────────────────────────

@dataclass
class InteroceptiveState:
    timestamp: float = field(default_factory=now)
    fatigue: float = 0.0                   # 0=energized 1=exhausted
    hunger: float = 0.0                    # 0=sated 1=ravenous
    arousal: float = 0.3                   # 0=calm 1=excited (bodily)
    pain: float = 0.0                      # 0=no pain 1=severe pain
    temperature: float = 0.5               # 0=cold 1=hot
    tension: float = 0.2                   # 0=relaxed 1=highly tense
    heartbeat_rapidity: float = 0.3        # 0=slow 1=racing
    breathing_rate: float = 0.3            # 0=slow 1=rapid

@dataclass
class ProprioceptiveState:
    timestamp: float = field(default_factory=now)
    position_x: float = 0.0
    position_y: float = 0.0
    orientation: float = 0.0               # radians
    velocity_linear: float = 0.0
    velocity_angular: float = 0.0
    embodied_orientation: str = ""         # e.g. "facing_north", "tilted"
    location_description: str = ""         # Semantic location label

@dataclass
class PerceptualFillState:
    timestamp: float = field(default_factory=now)
    gap_detected: bool = False
    gap_description: str = ""              # What sensory gap was detected
    filled_content: str = ""               # LLM-generated fill-in content
    confidence: float = 0.5                # 0=guess 1=confident
    fill_source: str = ""                  # Which modality triggered fill
    is_confabulatory: bool = False         # True if this is confabulatory

@dataclass
class TemporalCalibrationState:
    timestamp: float = field(default_factory=now)
    internal_clock_ms: float = 0.0         # Internal time counter
    drift_rate: float = 0.0                # Drift per second vs wall clock
    duration_estimate_ms: float = 0.0      # Estimated elapsed duration
    actual_duration_ms: float = 0.0        # Actual elapsed (if available)
    calibration_accuracy: float = 1.0      # 0=inaccurate 1=perfect


# ── Missing Unconscious Components ──────────────────────────────────────────

@dataclass
class CognitiveBiasState:
    timestamp: float = field(default_factory=now)
    confirmation_bias: float = 0.3         # 0=none 1=strong
    availability_bias: float = 0.3         # 0=none 1=strong
    anchoring_bias: float = 0.2            # 0=none 1=strong
    optimism_bias: float = 0.5             # 0=none 1=strong
    negativity_bias: float = 0.3           # 0=none 1=strong
    in_group_bias: float = 0.2             # 0=none 1=strong
    current_dominant_bias: str = ""        # Currently active bias
    neuromodulatory_influence: float = 0.3 # How much neuromodulators distort retrieval

@dataclass
class TraumaState:
    timestamp: float = field(default_factory=now)
    intrusion_active: bool = False         # Whether intrusive re-experiencing is active
    intrusion_content: str = ""            # Content of intrusion
    trigger: str = ""                      # What triggered the intrusion
    threat_level: float = 0.0              # 0=calm 1=overwhelming threat
    avoidance_active: bool = False         # Whether avoidance behaviors are active
    hypervigilance: float = 0.0            # 0=calm 1=extreme hypervigilance
    num_triggers_tracked: int = 0

@dataclass
class LateralInhibitionState:
    timestamp: float = field(default_factory=now)
    competition_active: bool = False       # Whether competition is occurring
    winning_signal: str = ""               # Which signal won
    inhibition_strength: float = 0.0       # 0=none 1=strong inhibition
    num_competitors: int = 0               # Number of competing signals
    winner_salience: float = 0.0           # Salience of winning signal

@dataclass
class TemporalBindingState:
    timestamp: float = field(default_factory=now)
    binding_window_ms: float = 500.0       # Current temporal binding window
    signals_bound: list = field(default_factory=list)  # Signals integrated
    coherence: float = 0.7                 # 0=fragmented 1=unified
    num_signals: int = 0                   # Number of signals in current window
    asynchrony_detected: bool = False      # Whether signals are out-of-sync

@dataclass
class SurpriseState:
    timestamp: float = field(default_factory=now)
    surprise_level: float = 0.0            # 0=none 1=maximum surprise
    novelty_level: float = 0.0             # 0=familiar 1=completely novel
    mismatch_magnitude: float = 0.0        # Prediction error that triggered this
    orienting_response: bool = False       # Whether orienting response was triggered
    source_modality: str = ""              # Which modality triggered surprise
    habituation_factor: float = 1.0        # 0=fully habituated 1=not habituated

@dataclass
class SemanticSatiationState:
    timestamp: float = field(default_factory=now)
    satiation_level: float = 0.0           # 0=none 1=complete satiation
    target_concept: str = ""               # Which concept is satiated
    repetition_count: int = 0              # How many repetitions contributed
    meaning_accessibility: float = 1.0     # 0=inaccessible 1=fully accessible
    recovery_progress: float = 0.0         # Recovery from satiation (0-1)

@dataclass
class MimicryState:
    timestamp: float = field(default_factory=now)
    mimicry_active: bool = False           # Whether mimicry is occurring
    mirrored_behavior: str = ""            # What behavior is being mirrored
    synchrony_level: float = 0.0           # 0=no synchrony 1=perfect synchrony
    resonance_intensity: float = 0.0       # 0=none 1=strong resonance
    target_agent: str = ""                 # Who is being mimicked
    automatic: bool = True                 # Whether this is automatic/unconscious


# ── Subconscious Extension ──────────────────────────────────────────────────

@dataclass
class AttachmentState:
    timestamp: float = field(default_factory=now)
    attachment_style: str = "secure"       # secure | anxious | avoidant | disorganized
    proximity_seeking: float = 0.5         # 0=avoidance 1=strong proximity seeking
    safe_base_confidence: float = 0.7      # 0=no safe base 1=secure base
    separation_distress: float = 0.2       # 0=calm 1=severe distress
    relational_trust: float = 0.6          # 0=no trust 1=complete trust
    fear_of_abandonment: float = 0.2       # 0=none 1=severe fear
    intimacy_comfort: float = 0.6          # 0=uncomfortable 1=comfortable with intimacy


# ── Qualia Extension ────────────────────────────────────────────────────────

@dataclass
class PhenomenalBindingState:
    timestamp: float = field(default_factory=now)
    binding_active: bool = False           # Whether binding is occurring
    bound_elements: list = field(default_factory=list)  # Elements being bound
    binding_coherence: float = 0.0         # 0=fragmented 1=perfectly bound
    modality_integration: float = 0.0      # Cross-modal integration (0-1)
    unity_quality: float = 0.0             # Phenomenal unity (0=disunity 1=unity)


# ── Missing Dreaming Components ─────────────────────────────────────────────

@dataclass
class MemoryReconsolidationState:
    timestamp: float = field(default_factory=now)
    reconsolidation_active: bool = False   # Whether reconsolidation is occurring
    memory_id: str = ""                    # Which memory is being reconsolidated
    modification_applied: str = ""         # What modification was made
    emotional_reappraisal: float = 0.0     # 0=no change 1=complete reappraisal
    destabilization_level: float = 0.0     # How destabilized the memory was
    re_stabilized: bool = False            # Whether memory was re-stabilized

@dataclass
class IncubationState:
    timestamp: float = field(default_factory=now)
    incubation_active: bool = False        # Whether incubation is active
    problem_content: str = ""              # What problem is incubating
    incubation_duration: float = 0.0       # How long incubation has lasted
    background_processing: str = ""        # Description of background processing
    insight_emerging: bool = False         # Whether insight is emerging
    activation_spreading: float = 0.0      # Spreading activation level (0-1)

@dataclass
class SchemaState:
    timestamp: float = field(default_factory=now)
    schema_id: str = ""                    # Identifier for the schema
    schema_content: str = ""               # Abstracted pattern/content
    abstraction_level: float = 0.5         # 0=concrete 1=highly abstract
    instances_encoded: int = 0             # How many instances formed this schema
    predictive_power: float = 0.5          # How well schema predicts (0-1)
    flexibility: float = 0.5               # 0=rigid 1=highly flexible

@dataclass
class NeuroplasticityState:
    timestamp: float = field(default_factory=now)
    plasticity_active: bool = False        # Whether plasticity is occurring
    pruning_intensity: float = 0.0         # Synaptic pruning (0-1)
    growth_intensity: float = 0.0          # Neural growth (0-1)
    target_region: str = ""                # Which functional region is affected
    long_term_potentiation: float = 0.0    # LTP analogue (0-1)
    structural_change: str = ""            # Description of structural change


# ── Affective Forecasting (flow-only in diagram) ────────────────────────────

@dataclass
class AffectiveForecastState:
    timestamp: float = field(default_factory=now)
    forecast_active: bool = False          # Whether forecasting is active
    target_event: str = ""                 # Event being forecast about
    predicted_valence: float = 0.5         # Predicted emotional valence (0-1)
    predicted_arousal: float = 0.3         # Predicted arousal (0-1)
    impact_bias: float = 0.3              # Overestimation of duration/intensity
    forecasting_horizon: float = 3600.0    # Seconds ahead being forecast
    confidence: float = 0.5                # Confidence in forecast (0-1)
