# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

GRACE AGi is a generative reasoning agentic cognitive engine designed for a wildlife/flower photography robot. It implements a full cognitive architecture pipeline with layers: Sensors → Unconscious → Subconscious → Conscience → Qualia → Conscious → Dreaming. Built on ROS2 Humble, runs on Jetson Orin Nano with Ollama/Nemotron LLM.

## Architecture
Refer to ROADMAP.md for the VitalCore Mermaid diagram. We are building a ROS 2 system for NVIDIA Jetson. Always prioritize uv for dependency management and keep nodes modular as per the diagram.

## Key Architectural Layers

1. **Sensors** - SensorHub publishes unified sensor bundles
2. **Unconscious** - Predictive processing, affective core, reward, relevance systems  
3. **Subconscious** - Memory systems (episodic, semantic, procedural, social)
4. **Conscience** - Moral reasoning based on scripture principles
5. **Qualia** - Phenomenal binding of experiences
6. **Conscious** - Global workspace theory with working memory, reflection, metacognition, executive function
7. **Dreaming** - Offline consolidation, imagination, distillation processes

All inter-node communication uses `std_msgs/String` carrying JSON payloads. No custom `.msg` files required.

## Development Commands

### Build & Install
```bash
# Build the package
cd ~/ros2_ws
colcon build --packages-select grace_agi --symlink-install
source install/setup.bash
```

### Run the System
```bash
# Full pipeline
source ~/ros2_ws/install/setup.bash
ros2 launch grace_agi grace_agi.launch.py

# Override model tag at runtime
ros2 launch grace_agi grace_agi.launch.py ollama_model:=nemotron:70b-instruct-q4_K_M

# Adjust moral strictness
ros2 launch grace_agi grace_agi.launch.py strictness:=0.95

# Trigger a dream cycle manually
ros2 topic pub --once /grace/dreaming/trigger std_msgs/String '{data: "trigger"}'
```

### Testing
```bash
# Run style/linter tests
pytest src/grace/test/test_flake8.py
pytest src/grace/test/test_pep257.py  
pytest src/grace/test/test_copyright.py

# Run all tests
pytest src/grace/test/
```

### Memory Setup (First Time)
```bash
mkdir -p /home/grace/memory
mkdir -p /home/grace/config
cp src/grace/config/scripture_principles.yaml /home/grace/config/
```

## Configuration

### Main Configuration (`src/grace/config/grace_agi.yaml`)
- Ollama host/model settings
- Topic names for all layers
- Timing frequencies (sensor_hz, unconscious_hz, etc.)
- Memory persistence paths
- Moral system strictness
- Nav2 integration toggle

### Scripture Principles (`src/grace/config/scripture_principles.yaml`)
Defines the moral framework used by the Conscience module for ethical evaluation.

## Important Topics

See README.md topic map for complete list, key ones include:
- `/grace/sensors/bundle` - Unified sensor data
- `/grace/unconscious/affective_state` - Emotional state (VAD)
- `/grace/conscious/global_workspace` - Winning conscious broadcast
- `/grace/conscience/verdict` - Moral decisions
- `/grace/action/log` - Action execution log
- `/cmd_vel` - Robot velocity commands
- `/grace/speech/out` - Text-to-speech output

## Node Count & SLM Nodes

Total: 34 nodes across all layers
SLM (LLM-powered) nodes: affective_core, social_cognition, moral_reasoning, conscience_core, qualia_binding, reflection, metacognition, central_executive, imagination

## Extending the System

- **Add sensors**: Publish to `/grace/sensors/bundle` or modify `sensor_hub.py`
- **Change morals**: Edit `scripture_principles.yaml` (no code changes)
- **Add actions**: Extend `action_execution.py` and update CentralExecutive prompt
- **Swap LLM**: Change `ollama_host`/`ollama_model` in launch or YAML