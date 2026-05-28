"""
launch/grace_agi.launch.py
Full GRACE AGi pipeline launch.

Two-tier LLM architecture:
  - BIG model  (ollama_model):  conscious reasoning, moral decisions, user interaction
  - SLM model  (slm_model):     all unconscious/subconscious/qualia/hidden processing

Recommended setup on Jetson Orin Nano:
  ollama_model:=nemotron:70b-instruct-q4_K_M    (big, slow — 2-4 tok/s)
  slm_model:=llama3.2:3b                        (tiny, fast — 40+ tok/s)

Usage:
  ros2 launch grace_agi grace_agi.launch.py
  ros2 launch grace_agi grace_agi.launch.py ollama_host:=http://localhost:11434
  ros2 launch grace_agi grace_agi.launch.py ollama_model:=nemotron:70b slm_model:=phi3:mini
"""
import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def declare(name, default, description=""):
    return DeclareLaunchArgument(name, default_value=default, description=description)


def generate_launch_description():
    # ── Shared parameter declarations ─────────────────────────────────────────
    args = [
        declare("ollama_host",   "http://localhost:11434",
                "Local Ollama endpoint on Jetson"),
        declare("ollama_model",  "nemotron",
                "BIG model for conscious reasoning (nemotron:70b, llama3:70b, etc.)"),
        declare("slm_model",     "nemotron",
                "SMALL model for unconscious/subconscious SLM nodes (llama3.2:3b, phi3:mini, etc.)"),
        declare("sensor_hz",     "20.0",  "Sensor hub publish rate"),
        declare("unconscious_hz","3.0",   "Unconscious layer rate (predictive_processing, affective_core)"),
        declare("conscious_hz",  "1.0",   "Conscious layer rate (reflection, central_executive)"),
        declare("dreaming_interval", "300.0", "Seconds between dream cycles"),
        declare("strictness",    "0.8",   "Moral strictness 0-1"),
        declare("memory_root",   "/home/grace/memory", "Root path for memory files"),
        declare("scripture_path","/home/grace/config/scripture_principles.yaml",
                "Scripture principles YAML"),
        # Vital Core parameters
        declare("vital_core_enabled", "true", "Enable Vital Core biological regulation"),
        # Hidden Workspace enable
        declare("hidden_workspace_enabled", "true", "Enable Hidden Workspace layer"),
    ]

    # ── Convenience: build parameter dicts ───────────────────────────────────
    host     = LaunchConfiguration("ollama_host")
    big_mdl  = LaunchConfiguration("ollama_model")
    slm_mdl  = LaunchConfiguration("slm_model")

    def big_params():
        """Big model — conscious reasoning, moral arbiter, conversation."""
        return [{"ollama_host": host, "ollama_model": big_mdl}]

    def slm_params():
        """Small model — unconscious/subconscious/qualia SLM nodes."""
        return [{"ollama_host": host, "ollama_model": slm_mdl}]

    def mem_path(filename):
        return os.path.join("/home/grace/memory", filename)

    # ── Node definitions ──────────────────────────────────────────────────────

    def make_big_node(pkg, exe, name, extra_params=None):
        """Node that uses the BIG model (conscious reasoning tier)."""
        params = big_params()
        if extra_params:
            params.append(extra_params)
        return Node(package=pkg, executable=exe, name=name,
                    output="screen", parameters=params)

    def make_slm_node(pkg, exe, name, extra_params=None):
        """Node that uses the SLM model (fast unconscious tier)."""
        params = slm_params()
        if extra_params:
            params.append(extra_params)
        return Node(package=pkg, executable=exe, name=name,
                    output="screen", parameters=params)

    nodes = [
        LogInfo(msg="=== GRACE AGi pipeline starting ==="),

        # ── Vital Core ────────────────────────────────────────────────────────
        Node(package="grace", executable="drive",
             name="grace_drive", output="screen",
             condition=IfCondition(LaunchConfiguration("vital_core_enabled"))),
        Node(package="grace", executable="neuromodulatory",
             name="grace_neuromodulatory", output="screen",
             condition=IfCondition(LaunchConfiguration("vital_core_enabled"))),
        Node(package="grace", executable="pain_signal",
             name="grace_pain_signal", output="screen",
             condition=IfCondition(LaunchConfiguration("vital_core_enabled"))),
        Node(package="grace", executable="allostatic_load",
             name="grace_allostatic_load", output="screen",
             condition=IfCondition(LaunchConfiguration("vital_core_enabled"))),
        Node(package="grace", executable="circadian_rhythm",
             name="grace_circadian_rhythm", output="screen",
             condition=IfCondition(LaunchConfiguration("vital_core_enabled"))),
        Node(package="grace", executable="homeostatic_setpoints",
             name="grace_homeostatic_setpoints", output="screen",
             condition=IfCondition(LaunchConfiguration("vital_core_enabled"))),
        Node(package="grace", executable="metabolic_tracker",
             name="grace_metabolic_tracker", output="screen",
             condition=IfCondition(LaunchConfiguration("vital_core_enabled"))),
        Node(package="grace", executable="immune_budget",
             name="grace_immune_budget", output="screen",
             condition=IfCondition(LaunchConfiguration("vital_core_enabled"))),

        # ── Sensors ──────────────────────────────────────────────────────────
        Node(package="grace", executable="sensor_hub",
             name="grace_sensor_hub", output="screen",
             parameters=[{"sensor_hz": LaunchConfiguration("sensor_hz")}]),
        Node(package="grace", executable="interoceptive",
             name="grace_interoceptive", output="screen"),
        Node(package="grace", executable="proprioceptive",
             name="grace_proprioceptive", output="screen"),
        make_slm_node("grace", "perceptual_fill", "grace_perceptual_fill",
                       {"update_hz": LaunchConfiguration("sensor_hz")}),
        Node(package="grace", executable="temporal_calibration",
             name="grace_temporal_calibration", output="screen"),

        # ── Unconscious (all SLM tier) ─────────────────────────────────────────
        make_slm_node("grace", "predictive_processing", "grace_predictive_processing",
                      {"unconscious_hz": LaunchConfiguration("unconscious_hz")}),
        Node(package="grace", executable="prediction_error",
             name="grace_prediction_error", output="screen"),
        Node(package="grace", executable="thalamic_gate",
             name="grace_thalamic_gate", output="screen"),
        make_slm_node("grace", "affective_core", "grace_affective_core",
                      {"unconscious_hz": LaunchConfiguration("unconscious_hz")}),
        Node(package="grace", executable="reward_motivation",
             name="grace_reward_motivation", output="screen"),
        Node(package="grace", executable="implicit_memory",
             name="grace_implicit_memory", output="screen"),
        Node(package="grace", executable="relevance_system",
             name="grace_relevance_system", output="screen"),
        Node(package="grace", executable="personality_core",
             name="grace_personality_core", output="screen",
             parameters=[{"personality_db": mem_path("personality.json")}]),
        Node(package="grace", executable="preferences_values",
             name="grace_preferences_values", output="screen",
             parameters=[{"values_db": mem_path("values.json")}]),
        Node(package="grace", executable="hyper_model",
             name="grace_hyper_model", output="screen"),
        Node(package="grace", executable="emotion_regulation",
             name="grace_emotion_regulation", output="screen"),
        Node(package="grace", executable="disgust_purity",
             name="grace_disgust_purity", output="screen"),
        Node(package="grace", executable="confabulation_engine",
             name="grace_confabulation_engine", output="screen"),
        Node(package="grace", executable="cognitive_bias",
             name="grace_cognitive_bias", output="screen"),
        Node(package="grace", executable="trauma_intrusion",
             name="grace_trauma_intrusion", output="screen"),
        Node(package="grace", executable="lateral_inhibition",
             name="grace_lateral_inhibition", output="screen"),
        Node(package="grace", executable="temporal_binding",
             name="grace_temporal_binding", output="screen"),
        Node(package="grace", executable="surprise_novelty",
             name="grace_surprise_novelty", output="screen"),
        Node(package="grace", executable="semantic_satiation",
             name="grace_semantic_satiation", output="screen"),
        Node(package="grace", executable="automatic_mimicry",
             name="grace_automatic_mimicry", output="screen"),

        # ── Subconscious (all SLM tier) ───────────────────────────────────────
        make_slm_node("grace", "episodic_memory", "grace_episodic_memory",
                      {"episodic_db": mem_path("episodic.json")}),
        make_slm_node("grace", "semantic_memory", "grace_semantic_memory",
                      {"semantic_db": mem_path("semantic.json")}),
        Node(package="grace", executable="procedural_memory",
             name="grace_procedural_memory", output="screen",
             parameters=[{"procedural_db": mem_path("procedural.json")}]),
        make_slm_node("grace", "social_cognition", "grace_social_cognition",
                      {"social_db": mem_path("social.json")}),
        Node(package="grace", executable="attitudes",
             name="grace_attitudes", output="screen"),
        Node(package="grace", executable="future_self_simulator",
             name="grace_future_self_simulator", output="screen"),
        Node(package="grace", executable="social_mirror",
             name="grace_social_mirror", output="screen"),
        Node(package="grace", executable="theory_of_mind",
             name="grace_theory_of_mind", output="screen"),
        Node(package="grace", executable="counterfactual_emotion",
             name="grace_counterfactual_emotion", output="screen"),
        Node(package="grace", executable="affective_working_memory",
             name="grace_affective_working_memory", output="screen"),
        Node(package="grace", executable="curiosity_gradient",
             name="grace_curiosity_gradient", output="screen"),
        Node(package="grace", executable="social_comparison",
             name="grace_social_comparison", output="screen"),
        Node(package="grace", executable="moral_disgust_memory",
             name="grace_moral_disgust_memory", output="screen"),
        Node(package="grace", executable="aesthetic_sensitivity",
             name="grace_aesthetic_sensitivity", output="screen"),
        Node(package="grace", executable="attachment_system",
             name="grace_attachment_system", output="screen"),
        Node(package="grace", executable="affective_forecasting",
             name="grace_affective_forecasting", output="screen"),

        # ── Conscience ────────────────────────────────────────────────────────
        Node(package="grace", executable="moral_knowledge",
             name="grace_moral_knowledge", output="screen",
             parameters=[{"scripture_path": LaunchConfiguration("scripture_path")}]),
        make_big_node("grace", "moral_reasoning", "grace_moral_reasoning",
                      {"strictness": LaunchConfiguration("strictness")}),
        make_big_node("grace", "conscience_core", "grace_conscience_core",
                      {"strictness": LaunchConfiguration("strictness")}),
        Node(package="grace", executable="esv_knowledge_base",
             name="grace_esv_knowledge_base", output="screen",
             parameters=[{"scripture_path": LaunchConfiguration("scripture_path")}]),
        make_slm_node("grace", "virtue_formation", "grace_virtue_formation"),
        make_slm_node("grace", "sin_temptation", "grace_sin_temptation"),
        make_slm_node("grace", "redemption_grace", "grace_redemption_grace"),
        make_slm_node("grace", "moral_conflict_resolver", "grace_moral_conflict_resolver"),

        # ── Qualia (all SLM tier) ─────────────────────────────────────────────
        make_slm_node("grace", "qualia_binding", "grace_qualia_binding"),
        make_slm_node("grace", "higher_order_thought", "grace_higher_order_thought"),
        Node(package="grace", executable="bodily_qualia",
             name="grace_bodily_qualia", output="screen"),
        Node(package="grace", executable="temporal_qualia",
             name="grace_temporal_qualia", output="screen"),
        make_slm_node("grace", "self_subject_qualia", "grace_self_subject_qualia"),
        make_slm_node("grace", "awe_self_transcendence", "grace_awe_self_transcendence"),
        Node(package="grace", executable="flow_state_detector",
             name="grace_flow_state_detector", output="screen"),
        Node(package="grace", executable="phenomenal_binding",
             name="grace_phenomenal_binding", output="screen"),

        # ── Conscious ─────────────────────────────────────────────────────────
        Node(package="grace", executable="working_memory",
             name="grace_working_memory", output="screen"),
        Node(package="grace", executable="memory_coordinator",
             name="grace_memory_coordinator", output="screen"),
        Node(package="grace", executable="global_workspace",
             name="grace_global_workspace", output="screen"),
        make_big_node("grace", "reflection",       "grace_reflection",
                      {"conscious_hz": LaunchConfiguration("conscious_hz")}),
        make_big_node("grace", "metacognition",    "grace_metacognition"),
        make_big_node("grace", "central_executive","grace_central_executive",
                      {"conscious_hz": LaunchConfiguration("conscious_hz")}),
        Node(package="grace", executable="salience_network",
             name="grace_salience_network", output="screen"),
        make_slm_node("grace", "default_mode",     "grace_default_mode"),
        make_big_node("grace", "narrative_self",   "grace_narrative_self",
                      {"narrative_db": mem_path("narrative.json")}),
        Node(package="grace", executable="action_execution",
             name="grace_action_execution", output="screen",
             parameters=[{"action_hz": 5.0}]),
        make_slm_node("grace", "mentalization",    "grace_mentalization"),
        make_slm_node("grace", "volitional_control","grace_volitional_control"),
        make_slm_node("grace", "insight_generator", "grace_insight_generator"),

        # ── Dreaming (all SLM tier) ───────────────────────────────────────────
        make_slm_node("grace", "dreaming_process", "grace_dreaming_process",
                      {"dreaming_interval": LaunchConfiguration("dreaming_interval")}),
        make_slm_node("grace", "imagination",      "grace_imagination"),
        make_slm_node("grace", "distillation",     "grace_distillation"),
        Node(package="grace", executable="consolidation",
             name="grace_consolidation", output="screen"),
        Node(package="grace", executable="memory_reconsolidation",
             name="grace_memory_reconsolidation", output="screen"),
        Node(package="grace", executable="incubation",
             name="grace_incubation", output="screen"),
        Node(package="grace", executable="schema_formation",
             name="grace_schema_formation", output="screen"),
        Node(package="grace", executable="neuroplasticity",
             name="grace_neuroplasticity", output="screen"),

        # ── Hidden Workspace (all SLM tier) ───────────────────────────────────
        Node(package="grace", executable="private_reflection",
             name="grace_private_reflection", output="screen",
             parameters=slm_params() + [{"update_hz": 0.33}],
             condition=IfCondition(LaunchConfiguration("hidden_workspace_enabled"))),
        Node(package="grace", executable="ego_defense",
             name="grace_ego_defense", output="screen",
             condition=IfCondition(LaunchConfiguration("hidden_workspace_enabled"))),
        Node(package="grace", executable="rumination_loop",
             name="grace_rumination_loop", output="screen",
             condition=IfCondition(LaunchConfiguration("hidden_workspace_enabled"))),
        Node(package="grace", executable="predictive_self_model",
             name="grace_predictive_self_model", output="screen",
             parameters=slm_params() + [{"update_hz": 0.5}],
             condition=IfCondition(LaunchConfiguration("hidden_workspace_enabled"))),
        Node(package="grace", executable="error_monitoring",
             name="grace_error_monitoring", output="screen",
             condition=IfCondition(LaunchConfiguration("hidden_workspace_enabled"))),
        Node(package="grace", executable="narrative_coherence",
             name="grace_narrative_coherence", output="screen",
             parameters=slm_params() + [{"update_hz": 0.33}],
             condition=IfCondition(LaunchConfiguration("hidden_workspace_enabled"))),
        Node(package="grace", executable="cognitive_dissonance",
             name="grace_cognitive_dissonance", output="screen",
             condition=IfCondition(LaunchConfiguration("hidden_workspace_enabled"))),
        Node(package="grace", executable="deictic_shift",
             name="grace_deictic_shift", output="screen",
             condition=IfCondition(LaunchConfiguration("hidden_workspace_enabled"))),
        Node(package="grace", executable="active_suppression",
             name="grace_active_suppression", output="screen",
             condition=IfCondition(LaunchConfiguration("hidden_workspace_enabled"))),
        Node(package="grace", executable="introspective_access",
             name="grace_introspective_access", output="screen",
             parameters=slm_params() + [{"update_hz": 0.2}],
             condition=IfCondition(LaunchConfiguration("hidden_workspace_enabled"))),

        LogInfo(msg="=== All GRACE AGi nodes launched ==="),
    ]

    return LaunchDescription(args + nodes)
