# VEILos4 Architecture Mapping

## Executive Summary

VEILos4 is a **quantum-cognitive operating system** with 5 core architectural layers:

1. **Quantum Substrate** - State superposition & coherence management
2. **Capability Security** - Fine-grained permission tokens
3. **Extensibility Framework** - Plugin architecture
4. **Cognitive Parity** - Equal interface for humans & models
5. **Audit & Transparency** - Immutable state logging

**Current Implementation State**: Prototype/MVP with working patterns but limited production hardening.

---

## 1. AGENT COORDINATION MECHANISMS

### 1.1 Messaging Bus (File-Based Pub/Sub)
**File**: `messaging_bus.py`

**Pattern**: Simulated pub/sub via JSON signal files in `mailbox/` directory

**Implementation**:
- `send_signal(target_agent, message)` - Write JSON to `mailbox/{agent_id}.signal.json`
- `receive_signal(agent_id)` - Read and consume signal file
- `list_pending_signals()` - Enumerate pending messages
- `clear_mailbox()` - Flush all signals

**Limitations**:
- File-based (not real-time)
- No ordering guarantees
- No acknowledgment mechanism
- Single-file per agent (no queue)

**What It Enables**:
- Asynchronous agent communication
- Decoupled agent orchestration
- Simple debugging (signals are readable JSON)

---

### 1.2 Thread Manager (Priority-Based Execution)
**File**: `thread_manager.py`

**Pattern**: YAML-defined thread specs with priority-based sequential execution

**Thread Spec Format** (`threads/*.thread.yaml`):
```yaml
name: quantum_supervisor
priority: 10
sequence:
  - "quantum_supervisor --drift"
  - "harmonizer_agent --engage"
  - "loop_manager --check"
```

**Implementation**:
- `load_thread_spec(thread_file)` - Parse YAML
- `run_thread(thread_file)` - Execute sequence via subprocess
- `run_parallel_threads(thread_files)` - Sort by priority, execute sequentially
- Subprocess-based (spawns `python3 veil_core.py <action>`)

**Limitations**:
- "Parallel" is actually sequential (sorted by priority)
- No inter-thread communication
- No failure recovery
- Subprocess overhead

**What It Enables**:
- Declarative task orchestration
- Priority-based scheduling
- LLM-interpretable task definitions

---

### 1.3 Agent Specifications (YAML-Based Triggers)
**Files**: `agents/*.agent.yaml`

**Example** (`echo_minder.agent.yaml`):
```yaml
agent_id: echo_minder
trigger: drift > 0.05
action: run_module
target: agent_harmonizer.py
persistence: recursive
max_cycles: 5
```

**Pattern**: Declarative agent definitions with trigger conditions

**Current Agents**:
- `echo_minder` - Monitors drift, triggers harmonizer
- `entropy_cleanser` - Cleans up state

**Limitations**:
- Triggers are not evaluated (just stored)
- No actual agent runtime
- No state machine

**What It Enables**:
- Human-readable agent definitions
- Trigger-based automation
- Recursive execution control

---

## 2. MULTI-PROVIDER INTEGRATION POINTS

### 2.1 Concierge OS Integration Layer
**Directory**: `concierge_os/integrations/`

**Providers Implemented**:

| Provider | File | Purpose |
|----------|------|---------|
| **LLM** | `llm_client.py` | Ollama or Grok-3 via xAI API |
| **Email** | `email_client.py` | SMTP-based email delivery |
| **SMS** | `sms_client.py` | Twilio-style SMS |
| **Voice** | `voice_client.py` | Piper TTS synthesis |
| **Image** | `image_client.py` | Stable Diffusion generation |
| **Web** | `web_client.py` | HTTP client wrapper |
| **Tunnel** | `tunnel.py` | Reverse tunnel for local services |

**LLM Client Pattern** (`llm_client.py`):
```python
def call_llm(messages: List[Dict[str, str]]) -> str:
    if settings.llm_backend == "grok":
        return _call_grok(messages)  # xAI API
    return _call_ollama(messages)    # Local Ollama
```

**Scheduler Integration** (`scheduler.py`):
- APScheduler-based async scheduling
- Cron triggers for recurring tasks
- Multi-channel delivery (email/SMS)
- Composite generation (text + image + voice)

**What It Enables**:
- Multi-modal agent capabilities
- Pluggable LLM backends
- Scheduled autonomous actions
- Provider abstraction

---

### 2.2 Agent Orchestrator (ReAct Loop)
**File**: `concierge_os/agent/orchestrator.py`

**Pattern**: Minimal ReAct-style loop

```python
def react_loop(user_message: str) -> str:
    # 1. Ask LLM for JSON instruction
    raw = call_llm(messages)
    parsed = json.loads(raw)
    
    # 2. Execute tool if requested
    if "tool" in parsed:
        result = registry.get(tool_name)(**tool_input)
    
    # 3. Return final response
    return parsed.get("final", result)
```

**Tool Registry** (`concierge_os/agent/tools.py`):
- Pluggable tool registry
- JSON-based tool invocation
- Result aggregation

**What It Enables**:
- LLM-driven agent autonomy
- Tool-use capability
- Structured reasoning loops

---

## 3. SELF-MODIFICATION SYSTEMS

### 3.1 VPatch - Runtime Patching Engine
**File**: `vpatch.py`

**Pattern**: File-based module patching with backup/rollback

**Operations**:
- `apply_patch(module_path, patch_path)` - Apply unified diff or direct replacement
- `create_patch(original, modified, output)` - Generate unified diff
- `validate_patch(module_path, patch_path)` - Dry-run validation
- `rollback_patch(module_path)` - Restore from `.backup`

**Limitations**:
- Direct file replacement (not true diff parsing)
- No atomic transactions
- No version tracking
- Backup only (no version history)

**What It Enables**:
- Runtime module updates
- Self-healing capabilities
- Patch validation before apply

---

### 3.2 Loop Manager (Recursive Correction)
**File**: `modules/loop_manager.py`

**Pattern**: Recursive depth-limited correction loop

```python
def run():
    mem = load_memory()
    depth = mem.get("loop_depth", 0)
    
    if depth >= MAX_DEPTH:  # MAX_DEPTH = 6
        return {"status": "limit_reached"}
    
    drift = mem.get("quantum", {}).get("drift", 0)
    
    if drift > 0.05:
        mem["loop_depth"] = depth + 1
        return {"status": "correction_initiated"}
    else:
        mem["loop_depth"] = 0
        return {"status": "stable"}
```

**What It Enables**:
- Recursive self-correction
- Depth-limited loops (prevents infinite recursion)
- Drift-based triggering

---

### 3.3 Agent Harmonizer (Drift Monitoring)
**File**: `modules/agent_harmonizer.py`

**Pattern**: Threshold-based module activation

```python
def run():
    drift = mem.get("quantum", {}).get("drift", 0)
    
    if drift > DRIFT_THRESHOLD:  # 0.05
        mem["action"] = "harmonizer_engaged"
    else:
        mem["action"] = "stable"
```

**What It Enables**:
- Autonomous drift correction
- Threshold-based activation
- State-driven behavior

---

## 4. QUANTUM/COGNITIVE PRIMITIVES

### 4.1 Quantum Substrate - Superposition Manager
**File**: `core/quantum/superposition.py`

**Pattern**: Quantum-inspired state superposition with collapse

**Key Classes**:
- `QuantumState` - Represents state with amplitude & phase
- `SuperpositionManager` - Manages multiple coexisting states

**Operations**:
```python
# Create superposition
superposition_id = quantum.create_superposition(
    "decision_001",
    states=[{"choice": "A"}, {"choice": "B"}],
    amplitudes=[0.7, 0.3]  # Probability amplitudes
)

# Observe (collapse)
collapsed = quantum.observe(superposition_id, observer_context)

# Entangle states
quantum.entangle(state_id1, state_id2)
```

**Implementation Details**:
- Amplitudes normalized to satisfy Born rule (sum of squares = 1)
- Collapse uses weighted random selection
- Entanglement cascades collapse to related states
- Observer callbacks on collapse

**What It Enables**:
- Multiple potential states coexisting
- Probabilistic decision-making
- Entanglement between operations
- Observer-dependent outcomes

---

### 4.2 Coherence Engine (Decoherence Prevention)
**File**: `core/quantum/coherence.py`

**Pattern**: Active coherence maintenance with error correction

**Key Classes**:
- `CoherenceMetrics` - Tracks coherence quality
- `CoherenceEngine` - Maintains state coherence

**Operations**:
```python
# Maintain coherence
coherence.maintain_coherence(state_id)

# Check if still coherent
is_coherent = coherence.check_coherence(state_id)

# Get metrics
metrics = coherence.get_metrics(state_id)
# Returns: coherence_time, decoherence_rate, fidelity, error_rate

# Extend coherence
coherence.extend_coherence_time(state_id, extension_seconds)
```

**Implementation Details**:
- Tracks coherence time per state
- Decoherence rate: 0.001 (1% per second)
- Fidelity = 1.0 - (elapsed * decoherence_rate)
- Error correction reduces error rate by 90%
- Configurable coherence_time (default 60s)

**What It Enables**:
- Preventing premature state collapse
- Quantum error correction
- Fidelity tracking
- Time-bounded coherence

---

### 4.3 Cognitive Parity Layer
**File**: `core/parity/unified_interface.py`

**Pattern**: Unified interface for humans and models

**Key Classes**:
- `Agent` - Represents human or model agent
- `AgentType` - HUMAN, MODEL, HYBRID, SYSTEM
- `ParityInterface` - Unified capability system
- `UnifiedToolInterface` - Unified tool access

**Operations**:
```python
# Register agent
agent = parity.register_agent(
    agent_id="user_001",
    agent_type=AgentType.HUMAN,
    capabilities=["read", "write"],
    metadata={"name": "Alice"}
)

# Invoke capability
result = parity.invoke_capability(
    agent_id="user_001",
    capability_name="read",
    resource="data.txt"
)

# Grant/revoke capability
parity.grant_capability("user_001", "admin")
parity.revoke_capability("user_001", "admin")

# Register tool
tools.register_tool(
    tool_name="search",
    tool_function=search_impl,
    description="Search documents",
    parameters={"query": "string"}
)

# Invoke tool
result = tools.invoke_tool("search", agent_id="user_001", query="quantum")
```

**What It Enables**:
- Equal capabilities for humans and models
- Unified tool interface
- Capability-based access control
- Agent type abstraction

---

## 5. AUTONOMOUS OPERATION PATTERNS

### 5.1 VEILed Daemon (Background Loop)
**File**: `valed.py`

**Pattern**: Continuous background loop with configurable interval

```python
def daemon_loop(interval=3, max_iterations=None):
    while True:
        result = loop_manager.run()
        
        if result.get("status") == "limit_reached":
            break
        
        if max_iterations and iteration >= max_iterations:
            break
        
        time.sleep(interval)
```

**CLI**:
```bash
python valed.py --interval 3 --max-iterations 100
```

**What It Enables**:
- Always-on background execution
- Configurable loop frequency
- Graceful shutdown (Ctrl+C)
- Iteration limits for testing

---

### 5.2 Foresight Engine (Predictive Simulation)
**File**: `foresight_engine.py`

**Pattern**: Next-state prediction based on current metrics

**Operations**:
```python
# Predict next state
prediction = predict_next_state()
# Returns: current_state, future_action, risk, confidence, recommendation

# Save prediction
pred_id = save_prediction(prediction)

# Compare to actual
comparison = compare_prediction_to_actual()
# Returns: accuracy, matched_metrics

# Generate report
report = generate_forecast_report()
```

**Prediction Logic**:
- If drift > 0.05: "spawn harmonizer" (risk: moderate, confidence: 0.75)
- If drift > 0.03: "monitor" (risk: low, confidence: 0.85)
- Else: "idle" (risk: minimal, confidence: 0.90)

**What It Enables**:
- Forward-looking decision making
- Accuracy tracking
- Risk assessment
- Confidence scoring

---

### 5.3 Introspector (State Capture & Analysis)
**File**: `introspector.py`

**Pattern**: Snapshot-based system introspection

**Operations**:
```python
# Capture state snapshot
frame = capture_state(memory_file, log_file)
# Saved to: stackframes/trace_YYYY-MM-DD-HH-MM-SS.json

# Analyze history
patterns = analyze_history(limit=10)

# Generate introspection report
report = generate_introspection_report()
```

**Frame Contents**:
- timestamp
- goal
- quantum metrics (drift, fidelity, coherence)
- current action
- stack depth hint
- metadata

**What It Enables**:
- System state snapshots
- Historical analysis
- Pattern detection
- Debugging traces

---

## 6. CORE SYSTEM INTEGRATION

### 6.1 VEIL4 Main System
**File**: `core/veil4_system.py`

**Pattern**: Unified orchestration of all layers

**Key Class**: `VEIL4`

**Initialization**:
```python
veil4 = VEIL4(config={"coherence_time": 60.0})
veil4.start()
```

**Components**:
- `quantum` - SuperpositionManager
- `coherence` - CoherenceEngine
- `security` - CapabilityManager
- `plugins` - PluginManager
- `parity` - ParityInterface
- `tools` - UnifiedToolInterface
- `audit` - ImmutableLog
- `provenance` - ProvenanceTracker

**What It Enables**:
- Unified system initialization
- Component orchestration
- Lifecycle management

---

## 7. MEMORY & STATE MANAGEMENT

### 7.1 Memory Store (JSON-Based)
**File**: `memory_store.json`

**Structure**:
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

**What It Enables**:
- Persistent state across runs
- Quantum metric tracking
- Action history
- Recursion depth tracking

---

## 8. ARCHITECTURE PATTERNS SUMMARY

| Pattern | Location | Type | Maturity |
|---------|----------|------|----------|
| **Messaging Bus** | `messaging_bus.py` | Coordination | Prototype |
| **Thread Manager** | `thread_manager.py` | Orchestration | Prototype |
| **Agent Specs** | `agents/*.yaml` | Declaration | Prototype |
| **LLM Integration** | `concierge_os/integrations/` | Provider | MVP |
| **ReAct Loop** | `concierge_os/agent/orchestrator.py` | Autonomy | MVP |
| **VPatch** | `vpatch.py` | Self-Modification | Prototype |
| **Loop Manager** | `modules/loop_manager.py` | Recursion | Prototype |
| **Harmonizer** | `modules/agent_harmonizer.py` | Correction | Prototype |
| **Superposition** | `core/quantum/superposition.py` | Quantum | MVP |
| **Coherence** | `core/quantum/coherence.py` | Quantum | MVP |
| **Parity** | `core/parity/unified_interface.py` | Parity | MVP |
| **VEILed Daemon** | `valed.py` | Autonomy | Prototype |
| **Foresight** | `foresight_engine.py` | Prediction | Prototype |
| **Introspector** | `introspector.py` | Introspection | Prototype |

---

## 9. CURRENT LIMITATIONS & GAPS

### Critical Issues
1. **No Real Concurrency** - Thread manager is sequential, not parallel
2. **File-Based Messaging** - No real-time pub/sub, no ordering
3. **No Failure Recovery** - No retry logic, no circuit breakers
4. **Limited Entanglement** - Quantum entanglement is simplified
5. **No Distributed Coordination** - Single-machine only
6. **Weak Agent Runtime** - Agent specs not evaluated at runtime

### Missing Patterns
- Event sourcing
- CQRS
- Saga pattern for distributed transactions
- Circuit breaker for fault tolerance
- Backpressure handling
- Rate limiting
- Distributed tracing

---

## 10. MODERNIZATION OPPORTUNITIES

### High Priority
1. **Replace file-based messaging** with Redis/RabbitMQ
2. **Implement true async/await** for concurrency
3. **Add distributed tracing** (OpenTelemetry)
4. **Implement event sourcing** for state management
5. **Add circuit breakers** for provider resilience

### Medium Priority
1. **Upgrade quantum simulation** (more realistic entanglement)
2. **Implement CQRS** for command/query separation
3. **Add saga pattern** for multi-step operations
4. **Implement backpressure** in message queues
5. **Add comprehensive logging** (structured logs)

### Low Priority
1. **Optimize performance** (caching, indexing)
2. **Add metrics/monitoring** (Prometheus)
3. **Implement rate limiting** per agent
4. **Add replay capability** for debugging

