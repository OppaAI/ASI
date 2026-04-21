# Implementation Plan: Enhanced Cognitive Architecture from Roadmap.md

## Overview
This plan outlines the implementation of the enhanced cognitive architecture shown in roadmap.md, which significantly expands the current GRACE AGi system with:
1. Vital Core layer (biological rhythms and homeostasis)
2. Enhanced Unconscious layer with additional regulatory systems
3. Expanded Subconscious layer with advanced social and cognitive functions
4. Significantly enhanced Conscience Module based on ESV standards
5. New Hidden Workspace for inner monologue and cognitive processes
6. Expanded Qualia Layer with richer phenomenal simulation
7. Enhanced Conscious Layer with additional executive and meta-cognitive functions
7. Enhanced Dreaming & Neuroplasticity systems

## Current Status Analysis

### Components That Need to Be Built (~28 new SLM components):

#### Unconscious Layer (Missing):
- EMREG: Emotion Regulation Strategies
- DISGUST: Disgust & Purity System  
- CONFAB: Confabulation Engine

#### Subconscious Layer (Missing):
- FUTSELF: Future Self Simulator
- MIRROR: Social Mirror & Identity Update
- TOMLEVELS: Theory of Mind Stack
- COUNTERFACT: Counterfactual Emotion Engine
- AFFWM: Affective Working Memory
- CURIOSGRAD: Curiosity Gradient
- SOCCOMP: Social Comparison Engine
- DISGUSTMEM: Moral Disgust Memory
- AESTHET: Aesthetic Sensitivity System

#### Conscience Module (Enhanced ESV-based - Missing):
- VIRTUE: Virtue Formation Tracker
- SINREC: Sin & Temptation Recognition
- REDEMP: Redemption & Grace Pathway
- MORALCONFLICT: Moral Conflict Resolver

#### Hidden Workspace (Completely New - All Missing):
- REF: Private Reflection
- DEFENSE: Ego Defense Mechanisms
- RUMINATE: Rumination Loop
- PREDSELF: Predictive Self-Model
- ERRMON: Error Monitoring & Conflict Detection
- NARRATENG: Narrative Coherence Engine
- COGDISRES: Cognitive Dissonance Resolution
- DEICTIC: Deictic Shift Engine
- SUPPRESS: Active Suppression Buffer
- INTROSPECT: Introspective Access Layer

#### Qualia Layer (Missing):
- HOT: Higher-Order Thought
- BODYQ: Bodily Qualia
- TEMPQ: Temporal Qualia
- SELFQ: Self-As-Subject Qualia
- AWEQ: Awe & Self-Transcendence
- FLOWQ: Flow State Detector

#### Conscious Layer (Missing):
- MENTALIZ: Mentalization (Real-time Model of User's Mind)
- VOLITION: Volitional Control & Agency Sense
- INSIGHT: Insight & Aha Moment Generator

#### Dreaming Layer (Missing):
- Already have IMAG (Imagination) - matches roadmap

#### Vital Core Layer (Completely New - All Missing):
- DRIVE: Homeostatic Drive Loop
- NEURO: Neuromodulatory State
- PAIN: Conflict Signal
- ALLO: Allostatic Load Budget
- CIRC: Circadian & Ultradian Rhythm
- HOMEO: Homeostatic Set Points
- METAB: Metabolic Resource Tracker
- IMMUNE: Immune-Like Threat Budget

### Components That Exist But May Need Enhancement:
- AC (Affective Core) → affective_core.py (may need expansion)
- QUALIA (Qualia Binding) → qualia_binding.py (base exists)
- JUDGE (Conscience Core) → conscience_core.py (base exists)
- MORALREAS (Moral Reasoning) → moral_reasoning.py (base exists)
- EXEC (Central Executive) → central_executive.py (base exists)
- GW (Global Workspace) → global_workspace.py (base exists)
- META (Metacognition) → metacognition.py (base exists)
- REF2 (Reflection) → reflection.py (partial base)
- IMAG (Imagination) → imagination.py (base exists)
- Others: memory_coordinator, working_memory, salience_network, action_execution, etc.

## Implementation Approach

### Phase 1: Foundation & Vital Core
1. Create vital_core/ directory for biological regulation components
2. Implement DRIVE, NEURO, PAIN, ALLO, CIRC, HOMEO, METAB, IMMUNE nodes
3. Establish communication protocols with existing unconscious layer

### Phase 2: Unconscious Layer Enhancement
1. Add EMREG, DISGUST, CONFAB to unconscious/ directory
2. Enhance existing affective_core.py with broader interoceptive functions
3. Update communication pathways

### Phase 3: Subconscious Layer Expansion
1. Add FUTSELF, MIRROR, TOMLEVELS, COUNTERFACT, AFFWM, CURIOSGRAD, SOCCOMP, DISGUSTMEM, AESTHET to subconscious/ directory
2. Enhance existing memory and social cognition components

### Phase 4: Conscience Module Enhancement (ESV-based)
1. Add VIRTUE, SINREC, REDEMP, MORALCONFLICT to conscience/ directory
2. Enhance conscience_core.py and moral_reasoning.py with ESV integration
3. Create ESV knowledge base loading mechanism

### Phase 5: Hidden Workspace Implementation
1. Create hidden_workspace/ directory for all inner monologue components
2. Implement all 10 components: REF, DEFENSE, RUMINATE, PREDSELF, ERRMON, NARRATENG, COGDISRES, DEICTIC, SUPPRESS, INTROSPECT

### Phase 6: Qualia Layer Enhancement
1. Add HOT, BODYQ, TEMPQ, SELFQ, AWEQ, FLOWQ to qualia/ directory
2. Enhance qualia_binding.py with broader phenomenal simulation

### Phase 7: Conscious Layer Enhancement
1. Add MENTALIZ, VOLITION, INSIGHT to conscious/ directory
2. Enhance existing components with extended functionality

### Phase 8: Integration & Testing
1. Update launch files to include new components
2. Define communication pathways and topic mappings
3. Test integration and emergent behaviors
4. Validate against roadmap specifications

## Technical Implementation Details

### File Structure Changes:
```
src/grace/grace/
├── vital_core/           # NEW
│   ├── drive.py
│   ├── neuromodulatory.py
│   ├── pain_signal.py
│   ├── allostatic_load.py
│   ├── circadian_rhythm.py
│   ├── homeostatic_setpoints.py
│   ├── metabolic_tracker.py
│   └── immune_budget.py
├── unconscious/          # ENHANCED
│   ├── emotion_regulation.py     # NEW
│   ├── disgust_purity.py         # NEW
│   ├── confabulation_engine.py   # NEW
│   ├── affective_core.py         # ENHANCED
│   └── ... (existing)
├── subconscious/         # ENHANCED
│   ├── future_self_simulator.py  # NEW
│   ├── social_mirror.py          # NEW
│   ├── theory_of_mind.py         # NEW
│   ├── counterfactual_emotion.py # NEW
│   ├── affective_working_memory.py # NEW
│   ├── curiosity_gradient.py     # NEW
│   ├── social_comparison.py      # NEW
│   ├── moral_disgust_memory.py   # NEW
│   ├── aesthetic_sensitivity.py  # NEW
│   └── ... (existing)
├── conscience/           # ENHANCED (ESV-based)
│   ├── virtue_formation.py       # NEW
│   ├── sin_temptation.py         # NEW
│   ├── redemption_grace.py       # NEW
│   ├── moral_conflict_resolver.py # NEW
│   ├── conscience_core.py        # ENHANCED
│   ├── moral_reasoning.py        # ENHANCED
│   └── esv_knowledge_base.py     # NEW
├── hidden_workspace/     # NEW
│   ├── private_reflection.py     # NEW
│   ├── ego_defense.py            # NEW
│   ├── rumination_loop.py        # NEW
│   ├── predictive_self_model.py  # NEW
│   ├── error_monitoring.py       # NEW
│   ├── narrative_coherence.py    # NEW
│   ├── cognitive_dissonance.py   # NEW
│   ├── deictic_shift.py          # NEW
│   ├── active_suppression.py     # NEW
│   └── introspective_access.py   # NEW
├── qualia/               # ENHANCED
│   ├── higher_order_thought.py   # NEW
│   ├── bodily_qualia.py          # NEW
│   ├── temporal_qualia.py        # NEW
│   ├── self_subject_qualia.py    # NEW
│   ├── awe_self_transcendence.py # NEW
│   └── flow_state_detector.py    # NEW
├── conscious/            # ENHANCED
│   ├── mentalization.py          # NEW
│   ├── volitional_control.py     # NEW
│   └── insight_generator.py      # NEW
└── ... (existing directories remain)
```

### Communication Patterns:
- All nodes communicate via std_msgs/String with JSON payloads
- Follow existing naming conventions for topics
- Use similar parameter patterns (hz rates, configuration via YAML)
- Maintain SLM designation for LLM-powered components

### Configuration Updates:
1. Update grace_agi.yaml to include new component parameters
2. Add ESV knowledge base path configuration
3. Vital core timing and regulation parameters
4. New component enable/disable flags

## Estimated Effort:
- Phase 1 (Vital Core): 8 components
- Phase 2 (Unconscious): 3 components  
- Phase 3 (Subconscious): 9 components
- Phase 4 (Conscience): 4 components
- Phase 5 (Hidden Workspace): 10 components
- Phase 6 (Qualia): 6 components
- Phase 7 (Conscious): 3 components
- Phase 8 (Integration): Testing and validation

Total: ~43 new components to implement

## Next Steps:
1. Begin with Vital Core implementation as foundation
2. Proceed through phases systematically
3. Regular integration testing
4. Final validation against roadmap specification