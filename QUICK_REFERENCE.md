# VEILos4 Quick Reference Guide

## File Location Index

### Core System
| Component | File | Lines | Purpose |
|-----------|------|-------|---------|
| Main System | `core/veil4_system.py` | 312 | Unified orchestration of all layers |
| Quantum Substrate | `core/quantum/superposition.py` | 209 | State superposition & collapse |
| Coherence Engine | `core/quantum/coherence.py` | 120 | Decoherence prevention |
| Parity Interface | `core/parity/unified_interface.py` | 241 | Unified human/model interface |
| Security | `core/security/capabilities.py` | ? | Capability-based access control |
| Audit Log | `core/audit/immutable_log.py` | ? | Immutable state logging |
| Extensibility | `core/extensibility/plugin_manager.py` | ? | Plugin framework |

### Coordination & Orchestration
| Component | File | Lines | Purpose |
|-----------|------|-------|---------|
| Messaging Bus | `messaging_bus.py` | 125 | File-based pub/sub |
| Thread Manager | `thread_manager.py` | 196 | Priority-based task orchestration |
| Agent Specs | `agents/*.agent.yaml` | 6 | Declarative agent definitions |

### Autonomy & Self-Modification
| Component | File | Lines | Purpose |
|-----------|------|-------|---------|
| Loop Manager | `modules/loop_manager.py` | 84 | Recursive correction loop |
| Harmonizer | `modules/agent_harmonizer.py` | 67 | Threshold-based activation |
| VPatch | `vpatch.py` | 171 | Runtime patching engine |
| VEILed Daemon | `valed.py` | 89 | Background loop daemon |

### Prediction & Introspection
| Component | File | Lines | Purpose |
|-----------|------|-------|---------|
| Foresight Engine | `foresight_engine.py` | 260 | State prediction |
| Introspector | `introspector.py` | 235 | State snapshots & analysis |

### Multi-Provider Integration
| Component | File | Purpose |
|-----------|------|---------|
| LLM Client | `concierge_os/integrations/llm_client.py` | Ollama/Grok-3 integration |
| Email Client | `concierge_os/integrations/email_client.py` | SMTP email delivery |
| SMS Client | `concierge_os/integrations/sms_client.py` | Twilio-style SMS |
| Voice Client | `concierge_os/integrations/voice_client.py` | Piper TTS synthesis |
| Image Client | `concierge_os/integrations/image_client.py` | Stable Diffusion |
| Web Client | `concierge_os/integrations/web_client.py` | HTTP wrapper |
| Tunnel | `concierge_os/integrations/tunnel.py` | Reverse tunnel |
| Scheduler | `concierge_os/scheduler.py` | APScheduler integration |
| Orchestrator | `concierge_os/agent/orchestrator.py` | ReAct loop |

### State & Configuration
| Component | File | Purpose |
|-----------|------|---------|
| Memory Store | `memory_store.json` | Persistent state |
| Config | `veilconfig.yaml` | System configuration |
| Manifest | `veil_manifest.yaml` | System manifest |
| Personality | `config/personality.yaml` | Agent personality |

### Thread & Task Definitions
| Component | File | Purpose |
|-----------|------|---------|
| Quantum Supervisor | `threads/quantum_supervisor.thread.yaml` | Quantum monitoring thread |
| System Monitor | `threads/system_monitor.thread.yaml` | System monitoring thread |
| Drift Report | `tasks/drift_report.task.yaml` | Drift reporting task |
| Repair Echo | `tasks/repair_echo.task.yaml` | Echo repair task |

---

## Key Patterns at a Glance

### Messaging
```python
# Send signal
send_signal("agent_id", {"event": "drift_detected", "value": 0.056})

# Receive signal
msg = receive_signal("agent_id")
```

### Thread Execution
```python
# Run single thread
result = run_thread("quantum_supervisor.thread.yaml")

# Run parallel threads (sorted by priority)
results = run_parallel_threads(["thread1.yaml", "thread2.yaml"])
```

### Quantum Operations
```python
# Create superposition
quantum.create_superposition("decision_001", 
    states=[{"choice": "A"}, {"choice": "B"}],
    amplitudes=[0.7, 0.3])

# Observe (collapse)
result = quantum.observe("decision_001", observer_context)

# Entangle states
quantum.entangle(state_id1, state_id2)
```

### Coherence Management
```python
# Maintain coherence
coherence.maintain_coherence(state_id)

# Check if coherent
is_coherent = coherence.check_coherence(state_id)

# Get metrics
metrics = coherence.get_metrics(state_id)
```

### Agent Parity
```python
# Register agents
parity.register_agent("user_001", AgentType.HUMAN, ["read", "write"])
parity.register_agent("model_gpt4", AgentType.MODEL, ["reason"])

# Invoke capability (same interface for both)
result = parity.invoke_capability("user_001", "read", resource="data.txt")
```

### Tool Interface
```python
# Register tool
tools.register_tool("search", search_impl, "Search documents", 
    parameters={"query": "string"})

# Invoke tool
result = tools.invoke_tool("search", agent_id="user_001", query="quantum")
```

### Patching
```python
# Apply patch
vpatch.apply_patch("modules/agent_harmonizer.py", "patches/fix.patch")

# Rollback
vpatch.rollback_patch("modules/agent_harmonizer.py")
```

### Prediction
```python
# Predict next state
prediction = foresight_engine.predict_next_state()

# Save prediction
pred_id = foresight_engine.save_prediction(prediction)

# Compare to actual
comparison = foresight_engine.compare_prediction_to_actual()
```

### Introspection
```python
# Capture state
frame = introspector.capture_state()

# Analyze history
patterns = introspector.analyze_history(limit=10)

# Generate report
report = introspector.generate_introspection_report()
```

---

## Architecture Layers

### Layer 1: Coordination
- **Messaging Bus**: File-based pub/sub
- **Thread Manager**: Priority-based orchestration
- **Agent Specs**: YAML-based triggers

### Layer 2: Autonomy
- **Loop Manager**: Recursive correction
- **Harmonizer**: Threshold-based activation
- **VEILed Daemon**: Background loop
- **Foresight Engine**: State prediction

### Layer 3: Quantum
- **Superposition Manager**: State coexistence
- **Coherence Engine**: Decoherence prevention

### Layer 4: Parity
- **Unified Agent Interface**: Equal capabilities
- **Unified Tool Interface**: Shared tools

### Layer 5: Observability
- **Introspector**: State snapshots
- **VPatch**: Runtime patching
- **Audit Log**: Immutable logging

---

## Configuration Files

### veilconfig.yaml
```yaml
# System configuration
coherence_time: 60.0
llm_backend: "ollama"  # or "grok"
ollama_base_url: "http://localhost:11434"
ollama_model: "mistral"
```

### Agent Specs (agents/*.agent.yaml)
```yaml
agent_id: echo_minder
trigger: drift > 0.05
action: run_module
target: agent_harmonizer.py
persistence: recursive
max_cycles: 5
```

### Thread Specs (threads/*.thread.yaml)
```yaml
name: quantum_supervisor
priority: 10
sequence:
  - "quantum_supervisor --drift"
  - "harmonizer_agent --engage"
  - "loop_manager --check"
```

---

## Memory Store Structure

```json
{
  "goal": "Awaiting injection",
  "quantum": {
    "drift": 0.056,
    "fidelity": 0.95,
    "coherence": 0.98
  },
  "action": "RECURSIVE_CORRECTION",
  "loop_depth": 2
}
```

---

## CLI Commands

### VEILed Daemon
```bash
python valed.py --interval 3 --max-iterations 100
```

### Thread Manager
```bash
python thread_manager.py quantum_supervisor.thread.yaml
python thread_manager.py --list
python thread_manager.py --parallel thread1.yaml thread2.yaml
```

### Foresight Engine
```bash
python foresight_engine.py
python foresight_engine.py --report
python foresight_engine.py --compare
```

### Introspector
```bash
python introspector.py
python introspector.py --report
```

### VPatch
```bash
python vpatch.py
```

---

## Key Metrics & Thresholds

### Quantum Metrics
- **Drift**: Quantum state deviation (0.0 - 1.0)
  - Threshold: 0.05 (triggers harmonizer)
  - Monitor threshold: 0.03
- **Fidelity**: State quality (0.0 - 1.0)
  - Decoherence rate: 0.001 (1% per second)
- **Coherence**: State coherence (0.0 - 1.0)
  - Default coherence time: 60 seconds

### Loop Metrics
- **Loop Depth**: Recursion depth
  - Max depth: 6 (prevents infinite loops)
  - Reset when drift < 0.05

### Prediction Metrics
- **Confidence**: Prediction confidence (0.0 - 1.0)
  - High drift (>0.05): 0.75
  - Medium drift (>0.03): 0.85
  - Low drift: 0.90

---

## Common Operations

### Start System
```python
from core.veil4_system import VEIL4

veil4 = VEIL4(config={"coherence_time": 60.0})
veil4.start()
```

### Register Agent
```python
veil4.register_agent(
    agent_id="user_001",
    agent_type=AgentType.HUMAN,
    capabilities=["read", "write"],
    metadata={"name": "Alice"}
)
```

### Create Quantum State
```python
veil4.create_quantum_state(
    state_id="decision_001",
    states=[
        {"choice": "option_a", "score": 0.7},
        {"choice": "option_b", "score": 0.3}
    ]
)
```

### Observe State
```python
result = veil4.observe_quantum_state("decision_001", "user_001")
```

### Grant Capability
```python
token = veil4.grant_capability(
    resource="data/documents",
    permissions=["read", "write"],
    agent_id="user_001",
    duration_seconds=3600
)
```

### Verify Access
```python
has_access = veil4.verify_access(
    agent_id="user_001",
    resource="data/documents",
    permission="read",
    capability_token=token
)
```

---

## Debugging Tips

### Check Memory State
```bash
cat memory_store.json | python -m json.tool
```

### View Pending Signals
```bash
ls -la mailbox/
```

### Check Stackframes
```bash
ls -la stackframes/
cat stackframes/trace_*.json | python -m json.tool
```

### View Futures (Predictions)
```bash
ls -la futures/
cat futures/pred_*.json | python -m json.tool
```

### Monitor Daemon
```bash
python valed.py --interval 1 --max-iterations 10
```

### Generate Forecast Report
```bash
python foresight_engine.py --report
```

### Capture Introspection
```bash
python introspector.py
```

---

## Performance Considerations

### Bottlenecks
1. **File I/O**: Messaging bus uses file writes (slow)
2. **Subprocess**: Thread manager spawns subprocesses (overhead)
3. **JSON Parsing**: Memory store uses JSON (not optimized)
4. **Polling**: Daemon uses sleep/poll (not event-driven)

### Optimization Opportunities
1. Replace file-based messaging with Redis
2. Use asyncio instead of subprocess
3. Use binary serialization (MessagePack, Protobuf)
4. Implement event-driven architecture

---

## Testing Checklist

- [ ] Messaging bus: send/receive signals
- [ ] Thread manager: run single and parallel threads
- [ ] Loop manager: test recursion depth limiting
- [ ] Harmonizer: test threshold-based activation
- [ ] Quantum: create/observe superpositions
- [ ] Coherence: maintain and check coherence
- [ ] Parity: register agents and invoke capabilities
- [ ] VPatch: apply and rollback patches
- [ ] Foresight: predict and compare states
- [ ] Introspector: capture and analyze frames

---

## Deployment Checklist

- [ ] Configure veilconfig.yaml
- [ ] Set up memory_store.json
- [ ] Create agent specs in agents/
- [ ] Create thread specs in threads/
- [ ] Create task specs in tasks/
- [ ] Set up logging
- [ ] Configure monitoring
- [ ] Set up alerting
- [ ] Test all components
- [ ] Document runbooks

