from setuptools import setup, find_packages
import os
from glob import glob

package_name = 'grace'

setup(
    name=package_name,
    version='1.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.py')),
        ('share/' + package_name + '/config', glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='GRACE',
    maintainer_email='grace@aurora.local',
    description='GRACE AGi — Full cognitive architecture pipeline',
    license='MIT',
    entry_points={
        'console_scripts': [
            # ── Sensors ──────────────────────────────────────────────
            'sensor_hub            = grace.sensor_hub:main',
            'interoceptive         = grace.sensors.interoceptive:main',
            'proprioceptive        = grace.sensors.proprioceptive:main',
            'perceptual_fill       = grace.sensors.perceptual_fill:main',
            'temporal_calibration  = grace.sensors.temporal_calibration:main',

            # ── Unconscious layer ────────────────────────────────────
            'predictive_processing = grace.unconscious.predictive_processing:main',
            'prediction_error      = grace.unconscious.prediction_error:main',
            'thalamic_gate         = grace.unconscious.thalamic_gate:main',
            'affective_core        = grace.unconscious.affective_core:main',
            'reward_motivation     = grace.unconscious.reward_motivation:main',
            'implicit_memory       = grace.unconscious.implicit_memory:main',
            'relevance_system      = grace.unconscious.relevance_system:main',
            'personality_core      = grace.unconscious.personality_core:main',
            'preferences_values    = grace.unconscious.preferences_values:main',
            'hyper_model           = grace.unconscious.hyper_model:main',
            'emotion_regulation    = grace.unconscious.emotion_regulation:main',
            'disgust_purity        = grace.unconscious.disgust_purity:main',
            'confabulation_engine  = grace.unconscious.confabulation_engine:main',
            'cognitive_bias        = grace.unconscious.cognitive_bias:main',
            'trauma_intrusion      = grace.unconscious.trauma_intrusion:main',
            'lateral_inhibition    = grace.unconscious.lateral_inhibition:main',
            'temporal_binding      = grace.unconscious.temporal_binding:main',
            'surprise_novelty      = grace.unconscious.surprise_novelty:main',
            'semantic_satiation    = grace.unconscious.semantic_satiation:main',
            'automatic_mimicry     = grace.unconscious.automatic_mimicry:main',

            # ── Subconscious layer ───────────────────────────────────
            'episodic_memory          = grace.subconscious.episodic_memory:main',
            'semantic_memory          = grace.subconscious.semantic_memory:main',
            'procedural_memory        = grace.subconscious.procedural_memory:main',
            'social_cognition         = grace.subconscious.social_cognition:main',
            'attitudes                = grace.subconscious.attitudes:main',
            'future_self_simulator    = grace.subconscious.future_self_simulator:main',
            'social_mirror            = grace.subconscious.social_mirror:main',
            'theory_of_mind           = grace.subconscious.theory_of_mind:main',
            'counterfactual_emotion   = grace.subconscious.counterfactual_emotion:main',
            'affective_working_memory = grace.subconscious.affective_working_memory:main',
            'curiosity_gradient       = grace.subconscious.curiosity_gradient:main',
            'social_comparison        = grace.subconscious.social_comparison:main',
            'moral_disgust_memory     = grace.subconscious.moral_disgust_memory:main',
            'aesthetic_sensitivity    = grace.subconscious.aesthetic_sensitivity:main',
            'attachment_system        = grace.subconscious.attachment_system:main',
            'affective_forecasting   = grace.subconscious.affective_forecasting:main',

            # ── Conscience module ────────────────────────────────────
            'moral_knowledge       = grace.conscience.moral_knowledge:main',
            'moral_reasoning       = grace.conscience.moral_reasoning:main',
            'conscience_core       = grace.conscience.conscience_core:main',
            'virtue_formation      = grace.conscience.virtue_formation:main',
            'sin_temptation        = grace.conscience.sin_temptation:main',
            'redemption_grace      = grace.conscience.redemption_grace:main',
            'moral_conflict_resolver = grace.conscience.moral_conflict_resolver:main',
            'esv_knowledge_base    = grace.conscience.esv_knowledge_base:main',

            # ── Qualia layer ─────────────────────────────────────────
            'qualia_binding        = grace.qualia.qualia_binding:main',
            'higher_order_thought  = grace.qualia.higher_order_thought:main',
            'bodily_qualia         = grace.qualia.bodily_qualia:main',
            'temporal_qualia       = grace.qualia.temporal_qualia:main',
            'self_subject_qualia   = grace.qualia.self_subject_qualia:main',
            'awe_self_transcendence = grace.qualia.awe_self_transcendence:main',
            'flow_state_detector   = grace.qualia.flow_state_detector:main',
            'phenomenal_binding    = grace.qualia.phenomenal_binding:main',

            # ── Conscious layer ──────────────────────────────────────
            'working_memory     = grace.conscious.working_memory:main',
            'memory_coordinator = grace.conscious.memory_coordinator:main',
            'global_workspace   = grace.conscious.global_workspace:main',
            'reflection         = grace.conscious.reflection:main',
            'metacognition      = grace.conscious.metacognition:main',
            'central_executive  = grace.conscious.central_executive:main',
            'salience_network   = grace.conscious.salience_network:main',
            'default_mode       = grace.conscious.default_mode:main',
            'narrative_self     = grace.conscious.narrative_self:main',
            'action_execution   = grace.conscious.action_execution:main',
            'conversation       = grace.conscious.conversation:main',
            'mentalization      = grace.conscious.mentalization:main',
            'volitional_control = grace.conscious.volitional_control:main',
            'insight_generator  = grace.conscious.insight_generator:main',

            # ── Dreaming / plasticity ────────────────────────────────
            'dreaming_process   = grace.dreaming.dreaming_process:main',
            'imagination        = grace.dreaming.imagination:main',
            'distillation       = grace.dreaming.distillation:main',
            'consolidation      = grace.dreaming.consolidation:main',
            'memory_reconsolidation = grace.dreaming.memory_reconsolidation:main',
            'incubation         = grace.dreaming.incubation:main',
            'schema_formation   = grace.dreaming.schema_formation:main',
            'neuroplasticity    = grace.dreaming.neuroplasticity:main',

            # ── Vital Core ───────────────────────────────────────────
            'drive              = grace.vital_core.drive:main',
            'neuromodulatory    = grace.vital_core.neuromodulatory:main',
            'pain_signal        = grace.vital_core.pain_signal:main',
            'allostatic_load    = grace.vital_core.allostatic_load:main',
            'circadian_rhythm   = grace.vital_core.circadian_rhythm:main',
            'homeostatic_setpoints = grace.vital_core.homeostatic_setpoints:main',
            'metabolic_tracker  = grace.vital_core.metabolic_tracker:main',
            'immune_budget      = grace.vital_core.immune_budget:main',

            # ── Hidden Workspace ─────────────────────────────────────
            'private_reflection      = grace.hidden_workspace.private_reflection:main',
            'ego_defense             = grace.hidden_workspace.ego_defense:main',
            'rumination_loop         = grace.hidden_workspace.rumination_loop:main',
            'predictive_self_model   = grace.hidden_workspace.predictive_self_model:main',
            'error_monitoring        = grace.hidden_workspace.error_monitoring:main',
            'narrative_coherence     = grace.hidden_workspace.narrative_coherence:main',
            'cognitive_dissonance    = grace.hidden_workspace.cognitive_dissonance:main',
            'deictic_shift           = grace.hidden_workspace.deictic_shift:main',
            'active_suppression      = grace.hidden_workspace.active_suppression:main',
            'introspective_access    = grace.hidden_workspace.introspective_access:main',
        ],
    },
)
