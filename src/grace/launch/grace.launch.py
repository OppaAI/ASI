"""
launch/grace.launch.py
Launches the full GRACE cognitive architecture.
Supports separate models for the cognitive pipeline and conversation.
"""
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, LogInfo, TimerAction
from launch.substitutions import LaunchConfiguration


def generate_launch_description():

    ollama_host_arg    = DeclareLaunchArgument(
        'ollama_host',    default_value='http://localhost:11434')
    pipeline_model_arg = DeclareLaunchArgument(
        'pipeline_model', default_value='gemma4:e2b')
    chat_model_arg     = DeclareLaunchArgument(
        'chat_model',     default_value='HammerAI/mn-mag-mell-r1:12b-q4_K_M')

    ollama_host    = LaunchConfiguration('ollama_host')
    pipeline_model = LaunchConfiguration('pipeline_model')
    chat_model     = LaunchConfiguration('chat_model')

    def pipeline_node(executable, extra_params=None, delay=0.0):
        n = Node(
            package='grace',
            executable=executable,
            name=executable,
            output='screen',
            parameters=[{
                'ollama_host':  ollama_host,
                'ollama_model': pipeline_model,
            }] + (extra_params or []),
        )
        return TimerAction(period=delay, actions=[n]) if delay > 0 else n

    def chat_node(delay=0.0):
        n = Node(
            package='grace',
            executable='conversation',
            name='conversation',
            output='screen',
            parameters=[{
                'ollama_host':  ollama_host,
                'ollama_model': chat_model,
            }],
        )
        return TimerAction(period=delay, actions=[n]) if delay > 0 else n

    return LaunchDescription([
        ollama_host_arg,
        pipeline_model_arg,
        chat_model_arg,

        LogInfo(msg="=== Launching GRACE AGI ==="),

        pipeline_node('sensor_hub'),

        pipeline_node('predictive_processing', delay=2.0),
        pipeline_node('prediction_error',      delay=2.0),
        pipeline_node('thalamic_gate',         delay=2.0),
        pipeline_node('affective_core',        delay=2.0),
        pipeline_node('reward_motivation',     delay=2.0),
        pipeline_node('implicit_memory',       delay=2.0),
        pipeline_node('relevance_system',      delay=2.0),
        pipeline_node('personality_core',      delay=2.0),
        pipeline_node('preferences_values',    delay=2.0),
        pipeline_node('hyper_model',           delay=2.0),

        pipeline_node('episodic_memory',       delay=4.0),
        pipeline_node('semantic_memory',       delay=4.0),
        pipeline_node('procedural_memory',     delay=4.0),
        pipeline_node('social_cognition',      delay=4.0),
        pipeline_node('attitudes',             delay=4.0),

        pipeline_node('moral_knowledge',       delay=6.0),
        pipeline_node('moral_reasoning',       delay=6.0),
        pipeline_node('conscience_core',       delay=6.0),

        pipeline_node('working_memory',        delay=8.0),
        pipeline_node('memory_coordinator',    delay=8.0),
        pipeline_node('salience_network',      delay=8.0),
        pipeline_node('global_workspace',      delay=8.0),
        pipeline_node('qualia_binding',        delay=8.0),
        pipeline_node('reflection',            delay=8.0),
        pipeline_node('metacognition',         delay=8.0),
        pipeline_node('default_mode',          delay=8.0),
        pipeline_node('narrative_self',        delay=8.0),
        pipeline_node('central_executive',     delay=8.0),
        pipeline_node('action_execution',      delay=8.0),

        chat_node(delay=8.0),

        pipeline_node('dreaming_process',      delay=10.0),
        pipeline_node('imagination',           delay=10.0),
        pipeline_node('distillation',          delay=10.0),
        pipeline_node('consolidation',         delay=10.0),

        LogInfo(msg="=== GRACE launch sequence complete ==="),
    ])