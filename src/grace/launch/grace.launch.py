"""
launch/grace.launch.py
Launches the full GRACE cognitive architecture.
"""
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, LogInfo, TimerAction
from launch.substitutions import LaunchConfiguration


def generate_launch_description():

    # ── Shared parameters ─────────────────────────────────────────────────────
    ollama_host  = LaunchConfiguration('ollama_host',  default='http://localhost:11434')
    ollama_model = LaunchConfiguration('ollama_model', default='nemotron')

    ollama_host_arg  = DeclareLaunchArgument('ollama_host',  default_value='http://localhost:11434')
    ollama_model_arg = DeclareLaunchArgument('ollama_model', default_value='nemotron')

    def ollama_params():
        return [{'ollama_host': ollama_host, 'ollama_model': ollama_model}]

    # ── Helper ────────────────────────────────────────────────────────────────
    def node(executable, extra_params=None, delay=0.0):
        n = Node(
            package='grace',
            executable=executable,
            name=executable,
            output='screen',
            parameters=ollama_params() + (extra_params or []),
        )
        if delay > 0:
            return TimerAction(period=delay, actions=[n])
        return n

    return LaunchDescription([
        ollama_host_arg,
        ollama_model_arg,

        LogInfo(msg="=== Launching GRACE AGI ==="),

        # ── Tier 0: Sensors (start immediately) ──────────────────────────────
        node('sensor_hub'),

        # ── Tier 1: Unconscious (needs sensors) ──────────────────────────────
        node('predictive_processing',  delay=2.0),
        node('prediction_error',       delay=2.0),
        node('thalamic_gate',          delay=2.0),
        node('affective_core',         delay=2.0),
        node('reward_motivation',      delay=2.0),
        node('implicit_memory',        delay=2.0),
        node('relevance_system',       delay=2.0),
        node('personality_core',       delay=2.0),
        node('preferences_values',     delay=2.0),
        node('hyper_model',            delay=2.0),

        # ── Tier 2: Subconscious (needs unconscious) ──────────────────────────
        node('episodic_memory',        delay=4.0),
        node('semantic_memory',        delay=4.0),
        node('procedural_memory',      delay=4.0),
        node('social_cognition',       delay=4.0),
        node('attitudes',              delay=4.0),

        # ── Tier 3: Conscience (needs subconscious) ───────────────────────────
        node('moral_knowledge',        delay=6.0),
        node('moral_reasoning',        delay=6.0),
        node('conscience_core',        delay=6.0),

        # ── Tier 4: Conscious (needs everything below) ────────────────────────
        node('working_memory',         delay=8.0),
        node('memory_coordinator',     delay=8.0),
        node('salience_network',       delay=8.0),
        node('global_workspace',       delay=8.0),
        node('qualia_binding',         delay=8.0),
        node('reflection',             delay=8.0),
        node('metacognition',          delay=8.0),
        node('default_mode',           delay=8.0),
        node('narrative_self',         delay=8.0),
        node('central_executive',      delay=8.0),
        node('action_execution',       delay=8.0),
        node('conversation',           delay=8.0),

        # ── Tier 5: Dreaming (runs in background, lowest priority) ────────────
        node('dreaming_process',       delay=10.0),
        node('imagination',            delay=10.0),
        node('distillation',           delay=10.0),
        node('consolidation',          delay=10.0),

        LogInfo(msg="=== GRACE launch sequence complete ==="),
    ])
