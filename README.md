# GRACE AGi — Generative Reasoning Agentic Cognitive Engine

Full cognitive architecture pipeline for the **GRACE** wildlife and flower
photography robot. Built on Waveshare UGV Beast / Jetson Orin Nano,
ROS2 Humble, and NVIDIA Nemotron via Ollama.

---

## Architecture overview

```
Sensors
  └── Unconscious  (predictive processing, affective core, reward, relevance)
        └── Subconscious  (episodic, semantic, procedural, social memory)
              ├── Conscience Module  (moral knowledge → reasoning → verdict)
              ├── Qualia Layer       (phenomenal binding)
              └── Conscious          (working memory → global workspace →
                                      reflection, metacognition, executive,
                                      salience, DMN, narrative self → action)
                    └── Dreaming     (dream → imagination → distillation
                                      → consolidation → back to all layers)
```

All inter-node communication uses `std_msgs/String` carrying JSON payloads.
No custom `.msg` files required.

---

## Hardware requirements

| Component | Spec |
|-----------|------|
| Platform  | Waveshare UGV Beast tracked chassis |
| Compute   | Jetson Orin Nano (8 GB) |
| LiDAR     | D500 |
| Depth cam | OAK-D |
| OS        | Ubuntu 22.04 (JetPack 6.x) |
| ROS2      | Humble |

---

## Software requirements

```bash
# ROS2 Humble (already installed on AuRoRA)
sudo apt install python3-colcon-common-extensions python3-pip
pip3 install requests pyyaml numpy
```

### Ollama + Nemotron on Jetson

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull Nemotron — check https://ollama.com/library/nemotron for available tags
ollama pull nemotron

# Verify it works
ollama run nemotron "Hello GRACE"

# Check the exact tag name you pulled — use that in grace_agi.yaml
ollama list
```

If you pulled a specific variant (e.g. `nemotron:70b-instruct-q4_K_M`), update
`config/grace_agi.yaml`:
```yaml
ollama:
  model: "nemotron:70b-instruct-q4_K_M"   # match exactly what `ollama list` shows
```

Or override at launch time:
```bash
ros2 launch grace_agi grace_agi.launch.py ollama_model:=nemotron:70b-instruct-q4_K_M
```

---

## Build & install

```bash
# On AuRoRA (Jetson)
cd ~/ros2_ws/src
cp -r /path/to/grace_agi .

cd ~/ros2_ws
colcon build --packages-select grace_agi --symlink-install
source install/setup.bash
```

---

## Create memory directories

```bash
mkdir -p /home/grace/memory
mkdir -p /home/grace/config

# Copy scripture principles to grace config dir
cp ~/ros2_ws/src/grace_agi/config/scripture_principles.yaml /home/grace/config/
```

---

## Run

### Full pipeline

```bash
source ~/ros2_ws/install/setup.bash
ros2 launch grace_agi grace_agi.launch.py
```

### Override model tag at runtime

```bash
ros2 launch grace_agi grace_agi.launch.py ollama_model:=nemotron:70b-instruct-q4_K_M
```

### Adjust moral strictness

```bash
ros2 launch grace_agi grace_agi.launch.py strictness:=0.95
```

### Trigger a dream cycle manually

```bash
ros2 topic pub --once /grace/dreaming/trigger std_msgs/String '{data: "trigger"}'
```

---

## Topic map (key topics)

| Topic | Direction | Content |
|-------|-----------|---------|
| `/grace/sensors/bundle` | SensorHub → all | Full sensor snapshot |
| `/grace/unconscious/affective_state` | AffectiveCore → all | VAD + emotion |
| `/grace/conscious/global_workspace` | GlobalWorkspace → all | Winning broadcast |
| `/grace/conscience/verdict` | ConscienceCore → Executive | Moral verdict |
| `/grace/conscious/executive_plan` | CentralExecutive → Action | Goal + steps |
| `/grace/action/log` | ActionExecution → all | What was done |
| `/grace/dreaming/consolidation` | Consolidation → all | Slow learning packet |
| `/cmd_vel` | ActionExecution → Nav2 | Drive commands |
| `/goal_pose` | ActionExecution → Nav2 | Navigation goals |
| `/grace/speech/out` | ActionExecution → TTS | Speech text |

---

## Node count

| Layer | Nodes |
|-------|-------|
| Sensors | 1 |
| Unconscious | 10 |
| Subconscious | 5 |
| Conscience | 3 |
| Qualia | 1 |
| Conscious | 10 |
| Dreaming | 4 |
| **Total** | **34** |

SLM (high-priority / LLM-powered) nodes: `affective_core`, `social_cognition`,
`moral_reasoning`, `conscience_core`, `qualia_binding`, `reflection`,
`metacognition`, `central_executive`, `imagination`.

---

## Systemd auto-start (optional)

```ini
# /etc/systemd/system/grace_agi.service
[Unit]
Description=GRACE AGi cognitive pipeline
After=network.target

[Service]
User=grace
Environment="OLLAMA_HOST=http://localhost:11434"
ExecStart=/bin/bash -c 'source /opt/ros/humble/setup.bash && \
  source /home/grace/ros2_ws/install/setup.bash && \
  ros2 launch grace_agi grace_agi.launch.py'
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable grace_agi
sudo systemctl start grace_agi
```

---

## Integration with ERIC / Nav2 stack

GRACE AGi is designed to run **alongside** your existing Nav2/SLAM stack.
It publishes to `/goal_pose` and `/cmd_vel` — the same topics Nav2 uses.
Set `nav2.enabled: true` in `config/grace_agi.yaml` to activate navigation
goal publishing from `CentralExecutive`.

The Conscience module will **veto** any navigation goal it judges unsafe
or immoral (e.g. approaching a person without consent) before it reaches
`/goal_pose`.

---

## Extending the architecture

- **Add a new sensor**: publish to `/grace/sensors/bundle` via SensorHub,
  or add a new subscription in `sensor_hub.py`.
- **Change moral principles**: edit `config/scripture_principles.yaml` —
  no code changes needed.
- **Add a new action**: add a branch in `action_execution.py`'s `_execute`
  method and add the action name to the `CentralExecutive` system prompt.
- **Swap the LLM**: change `ollama_host` + `ollama_model` in the launch
  command or YAML — the `OllamaClient` handles both Ollama and NVIDIA cloud.
