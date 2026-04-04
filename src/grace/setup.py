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
            'sensor_hub          = grace.sensor_hub:main',

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

            # ── Subconscious layer ───────────────────────────────────
            'episodic_memory    = grace.subconscious.episodic_memory:main',
            'semantic_memory    = grace.subconscious.semantic_memory:main',
            'procedural_memory  = grace.subconscious.procedural_memory:main',
            'social_cognition   = grace.subconscious.social_cognition:main',
            'attitudes          = grace.subconscious.attitudes:main',

            # ── Conscience module ────────────────────────────────────
            'moral_knowledge    = grace.conscience.moral_knowledge:main',
            'moral_reasoning    = grace.conscience.moral_reasoning:main',
            'conscience_core    = grace.conscience.conscience_core:main',

            # ── Qualia layer ─────────────────────────────────────────
            'qualia_binding     = grace.qualia.qualia_binding:main',

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

            # ── Dreaming / plasticity ────────────────────────────────
            'dreaming_process   = grace.dreaming.dreaming_process:main',
            'imagination        = grace.dreaming.imagination:main',
            'distillation       = grace.dreaming.distillation:main',
            'consolidation      = grace.dreaming.consolidation:main',
        ],
    },
)
