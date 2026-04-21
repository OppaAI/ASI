"""
launch/grace_agi.launch.py
Full GRACE AGi pipeline launch.

Usage:
  ros2 launch grace_agi grace_agi.launch.py
  ros2 launch grace_agi grace_agi.launch.py ollama_host:=http://localhost:11434

Override any parameter on the command line:
  ros2 launch grace_agi grace_agi.launch.py \
    ollama_model:=nemotron \
    dreaming_interval:=120.0
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
                "Model tag — must match what you pulled (ollama list)"),
        declare("sensor_hz",     "20.0",  "Sensor hub publish rate"),
        declare("unconscious_hz","10.0",  "Unconscious layer rate"),
        declare("conscious_hz",  "2.0",   "Conscious layer rate"),
        declare("dreaming_interval", "300.0", "Seconds between dream cycles"),
        declare("strictness",    "0.8",   "Moral strictness 0-1"),
        declare("memory_root",   "/home/grace/memory", "Root path for memory files"),
        declare("scripture_path","/home/grace/config/scripture_principles.yaml",
                "Scripture principles YAML"),
        # Vital Core parameters
        declare("vital_core_enabled", "true", "Enable Vital Core biological regulation"),
    ]

    # ── Convenience: build parameter dicts ───────────────────────────────────
    host  = LaunchConfiguration("ollama_host")
    model = LaunchConfiguration("ollama_model")

    def llm_params():
        return [{"ollama_host": host, "ollama_model": model}]

    def mem_path(filename):
        root = LaunchConfiguration("memory_root")
        return os.path.join("/home/grace/memory", filename)   # static for now

    # ── Node definitions ──────────────────────────────────────────────────────

    def make_node(pkg, exe, name, extra_params=None):
        params = llm_params()
        if extra_params:
            params.append(extra_params)
        return Node(package=pkg, executable=exe, name=name,
                    output="screen", parameters=params)

    def make_vital_node(pkg, exe, name):
        """Create a vital core node (non-LLM, parameter-free)"""
        return Node(package=pkg, executable=exe, name=name,
                    output="screen")

    nodes = [
        LogInfo(msg="=== GRACE AGi pipeline starting ==="),

        # ── Vital Core ────────────────────────────────────────────────────────
        # Conditionally load vital core components
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

        # ── Unconscious ───────────────────────────────────────────────────────
        make_node("grace_agi", "predictive_processing", "grace_predictive_processing",
                  {"unconscious_hz": LaunchConfiguration("unconscious_hz")}),
        Node(package="grace", executable="prediction_error",
             name="grace_prediction_error", output="screen"),
        Node(package="grace", executable="thalamic_gate",
             name="grace_thalamic_gate", output="screen"),
        make_node("grace_agi", "affective_core", "grace_affective_core",
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

        # ── Subconscious ──────────────────────────────────────────────────────
        make_node("grace_agi", "episodic_memory", "grace_episodic_memory",
                  {"episodic_db": mem_path("episodic.json")}),
        make_node("grace_agi", "semantic_memory", "grace_semantic_memory",
                  {"semantic_db": mem_path("semantic.json")}),
        Node(package="grace", executable="procedural_memory",
             name="grace_procedural_memory", output="screen",
             parameters=[{"procedural_db": mem_path("procedural.json")}]),
        make_node("grace_agi", "social_cognition", "grace_social_cognition",
                  {"social_db": mem_path("social.json")}),
        Node(package="grace", executable="attitudes",
             name="grace_attitudes", output="screen"),

        # ── Conscience ────────────────────────────────────────────────────────
        Node(package="grace", executable="moral_knowledge",
             name="grace_moral_knowledge", output="screen",
             parameters=[{"scripture_path": LaunchConfiguration("scripture_path")}]),
        make_node("grace_agi", "moral_reasoning", "grace_moral_reasoning",
                  {"strictness": LaunchConfiguration("strictness")}),
        make_node("grace_agi", "conscience_core", "grace_conscience_core",
                  {"strictness": LaunchConfiguration("strictness")}),

        # ── Qualia ────────────────────────────────────────────────────────────
        make_node("grace_agi", "qualia_binding", "grace_qualia_binding"),

        # ── Conscious ─────────────────────────────────────────────────────────
        Node(package="grace", executable="working_memory",
             name="grace_working_memory", output="screen"),
        Node(package="grace", executable="memory_coordinator",
             name="grace_memory_coordinator", output="screen"),
        Node(package="grace", executable="global_workspace",
             name="grace_global_workspace", output="screen"),
        make_node("grace_agi", "reflection",       "grace_reflection",
                  {"conscious_hz": LaunchConfiguration("conscious_hz")}),
        make_node("grace_agi", "metacognition",    "grace_metacognition"),
        make_node("grace_agi", "central_executive","grace_central_executive",
                  {"conscious_hz": LaunchConfiguration("conscious_hz")}),
        Node(package="grace", executable="salience_network",
             name="grace_salience_network", output="screen"),
        make_node("grace_agi", "default_mode",     "grace_default_mode"),
        make_node("grace_agi", "narrative_self",   "grace_narrative_self",
                  {"narrative_db": mem_path("narrative.json")}),
        Node(package="grace", executable="action_execution",
             name="grace_action_execution", output="screen",
             parameters=[{"action_hz": 5.0}]),

        # ── Dreaming ──────────────────────────────────────────────────────────
        make_node("grace_agi", "dreaming_process", "grace_dreaming_process",
                  {"dreaming_interval": LaunchConfiguration("dreaming_interval")}),
        make_node("grace_agi", "imagination",      "grace_imagination"),
        make_node("grace_agi", "distillation",     "grace_distillation"),
        Node(package="grace", executable="consolidation",
             name="grace_consolidation", output="screen"),

        LogInfo(msg="=== All GRACE AGi nodes launched ==="),
    ]

    return LaunchDescription(args + nodes)
