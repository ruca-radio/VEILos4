# VEILos4 Modernization Architecture

**Version:** 1.0  
**Date:** 2025-02-25  
**Status:** PROPOSAL

## Executive Summary

Transform VEILos from a theoretical prompt injection technique into a production-grade autonomous multi-model orchestration platform by adopting proven OpenClaw patterns while preserving VEILos's unique quantum-cognitive substrate.

---

## Current State Assessment

### What Works ✅
- **VEIL4 Core**: Solid quantum-cognitive OS layer (31/31 tests passing)
- **Capability Security**: Fine-grained permission model implemented
- **Audit System**: Immutable logging operational
- **Plugin Framework**: Hot-swap extensibility works
- **Quantum Substrate**: Superposition/coherence/entanglement primitives functional

### What Needs Replacement ❌
- **LLM Integration**: Simple if/else provider switching (`llm_client.py`)
- **Orchestration**: Minimal single-turn ReAct loop (`orchestrator.py`)
- **Agent Execution**: YAML definitions exist but no execution engine
- **Multi-Model**: Sequential provider switching, not parallel orchestration
- **Autonomous Operation**: Missing self-extending/self-monitoring capabilities

### Critical Gap
**No production-ready orchestration layer** connecting VEIL4 Core to real agentic workflows.

---

## Modernization Strategy

### Design Principles

1. **Preserve Differentiation**: Keep VEILos's unique quantum substrate, cognitive mapping, and equal plane
2. **Adopt Proven Patterns**: Use OpenClaw's Gateway, Lane Queue, Provider Abstraction
3. **Production First**: Every component must be deployable, monitorable, recoverable
4. **Autonomous by Default**: Self-extending, self-monitoring, self-healing as core features

### Three-Layer Architecture (Enhanced)

```
┌────────────────────────────────────────────────────────────┐
│                    SURFACE LAYER                           │
│  Terminal │ API Gateway │ Channel Adapters │ WebUI        │
└───────────────────────┬────────────────────────────────────┘
                        │
┌───────────────────────┴────────────────────────────────────┐
│              ORCHESTRATION LAYER (NEW)                     │
│  ┌──────────────────────────────────────────────────────┐ │
│  │          Gateway (Routing & Session)                 │ │
│  ├──────────────────────────────────────────────────────┤ │
│  │          Lane Queue (Serial Execution)               │ │
│  ├──────────────────────────────────────────────────────┤ │
│  │     Provider Abstraction (Multi-Model Router)        │ │
│  ├──────────────────────────────────────────────────────┤ │
│  │     Agent Execution Engine (YAML → Runtime)          │ │
│  ├──────────────────────────────────────────────────────┤ │
│  │   Autonomous Coordinator (Self-Extend/Monitor/Heal)  │ │
│  └──────────────────────────────────────────────────────┘ │
└───────────────────────┬────────────────────────────────────┘
                        │
┌───────────────────────┴────────────────────────────────────┐
│                  VEIL4 CORE (PRESERVED)                    │
│  Quantum Substrate │ Security │ Parity │ Audit │ Plugins  │
└───────────────────────┬────────────────────────────────────┘
                        │
┌───────────────────────┴────────────────────────────────────┐
│                  COGNITIVE LAYER                           │
│  OpenAI │ Anthropic │ Google │ Ollama │ Custom Models     │
└────────────────────────────────────────────────────────────┘
```

---

## Component Design

### 1. Gateway Layer

**Purpose**: Single entry point for all requests with routing, authentication, session management.

**Responsibilities**:
- Normalize inputs from channels (HTTP, WebSocket, CLI, IPC)
- Route to appropriate agent/session
- Enforce authentication/authorization via VEIL4 capability system
- Maintain session state and history

**Implementation**:
```python
# orchestration/gateway.py
class Gateway:
    def __init__(self, veil4_core, lane_queue):
        self.veil4 = veil4_core
        self.lanes = lane_queue
        self.sessions = {}  # session_id -> Session
        
    async def handle_request(self, request: Request) -> Response:
        # 1. Authenticate via VEIL4 capability tokens
        agent_id = self.veil4.authenticate(request.token)
        
        # 2. Get or create session
        session = self.get_session(agent_id, request.channel)
        
        # 3. Submit to lane queue
        task = Task(
            agent_id=agent_id,
            message=request.message,
            session=session,
            context=request.context
        )
        result = await self.lanes.submit(task)
        
        # 4. Return response
        return Response(result)
```

**Integration Points**:
- ✅ Uses VEIL4 capability tokens for auth
- ✅ Routes through quantum substrate for state management
- ✅ Audit log for all requests

---

### 2. Lane Queue System

**Purpose**: Serial-by-default execution to prevent race conditions and state corruption.

**Design**:
- Each session gets dedicated lane (queue)
- FIFO execution within lane
- Explicit parallel opt-in for idempotent tasks
- Backpressure control

**Implementation**:
```python
# orchestration/lane_queue.py
class LaneQueue:
    def __init__(self, max_parallel_lanes=10):
        self.lanes = {}  # session_id -> asyncio.Queue
        self.executors = {}  # session_id -> asyncio.Task
        self.semaphore = asyncio.Semaphore(max_parallel_lanes)
        
    async def submit(self, task: Task) -> Result:
        # Get or create lane for session
        lane = self.get_or_create_lane(task.session.id)
        
        # Enqueue task
        future = asyncio.Future()
        await lane.put((task, future))
        
        # Ensure executor running
        self.ensure_executor(task.session.id)
        
        # Wait for result
        return await future
        
    async def _executor(self, session_id: str):
        lane = self.lanes[session_id]
        async with self.semaphore:
            while True:
                task, future = await lane.get()
                try:
                    result = await self._execute_task(task)
                    future.set_result(result)
                except Exception as e:
                    future.set_exception(e)
```

**Benefits**:
- Prevents concurrent modification bugs
- Predictable execution order
- Natural backpressure
- Easy to reason about

---

### 3. Provider Abstraction Layer

**Purpose**: Unified interface to multiple LLM providers with fallback chains and cost-aware routing.

**Architecture**:
```
┌─────────────────────────────────────────────────────┐
│              Provider Router                        │
│  (Model Selection, Fallback, Rate Limiting)         │
└──────────────┬──────────────────────────────────────┘
               │
     ┌─────────┼─────────┬──────────┬──────────┐
     │         │         │          │          │
┌────▼───┐ ┌──▼────┐ ┌──▼─────┐ ┌──▼─────┐ ┌─▼──────┐
│OpenAI  │ │Anthropic│ │Google │ │Ollama  │ │Custom │
│Adapter │ │ Adapter │ │Adapter│ │Adapter │ │Adapter│
└────────┘ └─────────┘ └────────┘ └────────┘ └────────┘
```

**Implementation**:
```python
# orchestration/providers/router.py
class ProviderRouter:
    def __init__(self, veil4_core):
        self.veil4 = veil4_core
        self.adapters = {
            "openai": OpenAIAdapter(),
            "anthropic": AnthropicAdapter(),
            "google": GoogleAdapter(),
            "ollama": OllamaAdapter(),
        }
        self.fallback_chains = {
            "default": ["openai", "anthropic", "ollama"],
            "cheap": ["ollama", "openai"],
            "premium": ["anthropic", "openai"],
        }
        
    async def complete(self, messages, strategy="default", **kwargs):
        chain = self.fallback_chains.get(strategy, self.fallback_chains["default"])
        
        for provider in chain:
            adapter = self.adapters[provider]
            
            # Check rate limits
            if adapter.is_rate_limited():
                continue
                
            try:
                # Use quantum superposition for provider selection
                state_id = f"provider_{uuid4()}"
                self.veil4.create_quantum_state(
                    state_id,
                    [{"provider": p, "score": self._score_provider(p)} 
                     for p in chain]
                )
                
                result = await adapter.complete(messages, **kwargs)
                
                # Collapse quantum state to actual provider used
                self.veil4.observe_quantum_state(state_id, provider)
                
                return result
                
            except Exception as e:
                self.veil4.audit_log({
                    "event": "provider_failed",
                    "provider": provider,
                    "error": str(e)
                })
                continue
                
        raise ProviderExhaustionError("All providers failed")
        
    def _score_provider(self, provider):
        # Cost, latency, reliability scoring
        pass
```

**Key Features**:
- ✅ Unified API across providers
- ✅ Automatic fallback on failure
- ✅ Rate limit aware
- ✅ Cost-based routing
- ✅ Integrated with quantum substrate for provider selection superposition

---

### 4. Agent Execution Engine

**Purpose**: Execute YAML-defined agents with full lifecycle management.

**YAML Agent Format** (existing):
```yaml
# agents/research_agent.yaml
name: research_agent
description: Deep research and analysis
triggers:
  - pattern: "research.*"
    channel: "cli"
actions:
  - type: "llm_call"
    provider: "anthropic"
    model: "claude-3-5-sonnet"
  - type: "tool_call"
    tools: ["search", "scrape", "summarize"]
memory:
  type: "hybrid"
  sources: ["semantic_index", "keyword_index"]
capabilities:
  - "read:documents"
  - "write:notes"
```

**Execution Engine**:
```python
# orchestration/agent_engine.py
class AgentExecutionEngine:
    def __init__(self, veil4_core, provider_router, tool_registry):
        self.veil4 = veil4_core
        self.providers = provider_router
        self.tools = tool_registry
        self.agents = {}  # agent_id -> AgentRuntime
        
    async def load_agent(self, agent_yaml_path: Path):
        spec = yaml.safe_load(agent_yaml_path.read_text())
        
        # Verify capabilities via VEIL4
        for cap in spec["capabilities"]:
            if not self.veil4.verify_capability(cap):
                raise CapabilityError(f"Agent lacks capability: {cap}")
        
        # Create runtime
        runtime = AgentRuntime(
            spec=spec,
            provider_router=self.providers,
            tool_registry=self.tools,
            memory=self._load_memory(spec["memory"])
        )
        
        self.agents[spec["name"]] = runtime
        
        # Register triggers
        for trigger in spec["triggers"]:
            self.veil4.register_trigger(
                pattern=trigger["pattern"],
                handler=lambda msg: self.execute(spec["name"], msg)
            )
        
    async def execute(self, agent_id: str, message: str) -> str:
        runtime = self.agents[agent_id]
        
        # Agentic loop: ReAct pattern
        max_iterations = 10
        for i in range(max_iterations):
            # 1. Retrieve memory
            context = await runtime.memory.retrieve(message)
            
            # 2. LLM call
            response = await self.providers.complete(
                messages=runtime.build_messages(message, context),
                strategy="default"
            )
            
            # 3. Parse action
            action = self._parse_action(response)
            
            if action["type"] == "final":
                return action["content"]
            
            # 4. Execute tool
            tool_result = await self.tools.execute(
                action["tool"],
                action["input"]
            )
            
            # 5. Update memory
            runtime.memory.add(f"Tool {action['tool']}: {tool_result}")
            
        return "Max iterations reached"
```

**Benefits**:
- ✅ Declarative agent definitions
- ✅ Automatic capability checking
- ✅ Memory-first pattern
- ✅ Tool integration
- ✅ Full audit trail

---

### 5. Autonomous Coordinator

**Purpose**: Self-extending, self-monitoring, self-healing system that operates without human intervention.

**Capabilities**:
1. **Self-Extend**: Dynamically load plugins and agents based on detected needs
2. **Self-Monitor**: Track system health, performance, errors
3. **Self-Heal**: Automatic recovery from failures

**Implementation**:
```python
# orchestration/autonomous_coordinator.py
class AutonomousCoordinator:
    def __init__(self, veil4_core, agent_engine):
        self.veil4 = veil4_core
        self.agents = agent_engine
        self.health_monitor = HealthMonitor()
        self.plugin_discoverer = PluginDiscoverer()
        
    async def run(self):
        while True:
            # 1. Monitor system health
            health = await self.health_monitor.check_all()
            
            if health["status"] != "healthy":
                await self.heal(health["issues"])
            
            # 2. Discover needed capabilities
            needs = await self.analyze_needs()
            
            if needs:
                await self.extend(needs)
            
            # 3. Optimize performance
            await self.optimize()
            
            await asyncio.sleep(60)  # Check every minute
            
    async def heal(self, issues: List[Issue]):
        for issue in issues:
            if issue.type == "agent_crashed":
                # Restart agent
                await self.agents.restart(issue.agent_id)
                
            elif issue.type == "provider_down":
                # Switch to fallback provider
                self.veil4.update_config({
                    "primary_provider": issue.fallback_provider
                })
                
            elif issue.type == "resource_exhaustion":
                # Scale resources
                await self.scale_up(issue.resource_type)
                
    async def extend(self, needs: List[Need]):
        for need in needs:
            if need.type == "missing_tool":
                # Discover and load tool plugin
                plugin = await self.plugin_discoverer.find_tool(need.tool_name)
                if plugin:
                    await self.veil4.load_plugin(plugin)
                    
            elif need.type == "missing_agent":
                # Generate or download agent definition
                agent_spec = await self.generate_agent_spec(need)
                await self.agents.load_agent(agent_spec)
                
    async def optimize(self):
        # Analyze performance metrics
        metrics = self.veil4.get_metrics()
        
        # Adjust routing strategy
        if metrics["avg_latency"] > 1000:  # ms
            self.veil4.set_provider_strategy("cheap")
        
        # Prune unused agents
        inactive = [a for a in self.agents if a.last_used > 7*24*3600]
        for agent_id in inactive:
            await self.agents.unload(agent_id)
```

**Benefits**:
- ✅ Autonomous operation
- ✅ Self-healing
- ✅ Dynamic capability extension
- ✅ Performance optimization

---

## Integration with VEIL4 Core

### Quantum Substrate Integration

**Use Cases**:
1. **Provider Selection**: Maintain providers in superposition until observation
2. **Multi-Agent Coordination**: Entangle related agent states
3. **Decision Making**: Represent uncertain choices as superposed states

```python
# Example: Quantum provider selection
state_id = f"provider_selection_{task_id}"
veil4.create_quantum_state(
    state_id,
    states=[
        {"provider": "openai", "confidence": 0.6},
        {"provider": "anthropic", "confidence": 0.4}
    ]
)

# Collapse when actual call made
chosen = veil4.observe_quantum_state(state_id, context=task_context)
result = await provider_router.complete(messages, provider=chosen["provider"])
```

### Capability Security Integration

**All operations go through VEIL4's capability system**:
```python
# Agent requests capability token
token = veil4.grant_capability(
    resource="tools/search",
    permissions=["execute"],
    agent_id=agent_id,
    duration_seconds=3600
)

# Tool execution verifies token
if not veil4.verify_access(agent_id, "tools/search", "execute", token):
    raise PermissionDenied()
```

### Audit Integration

**Every operation logged**:
```python
veil4.audit_log({
    "event": "agent_execution",
    "agent_id": agent_id,
    "task": task,
    "provider": provider,
    "tools_called": tool_calls,
    "result": result,
    "timestamp": time.time()
})
```

---

## Migration Path

### Phase 1: Foundation (Week 1)
- [ ] Implement Gateway layer
- [ ] Implement Lane Queue system
- [ ] Create Provider Abstraction interfaces
- [ ] Tests: Gateway routing, Lane execution order, Provider failover

### Phase 2: Orchestration (Week 2)
- [ ] Implement Provider Router with OpenAI, Anthropic, Ollama adapters
- [ ] Build Agent Execution Engine
- [ ] Load existing YAML agents
- [ ] Tests: Multi-provider calls, Agent execution, Tool integration

### Phase 3: Autonomous Operation (Week 3)
- [ ] Implement Autonomous Coordinator
- [ ] Add health monitoring
- [ ] Add self-healing
- [ ] Add self-extension
- [ ] Tests: Failure recovery, Plugin discovery, Performance optimization

### Phase 4: Production Hardening (Week 4)
- [ ] Containerization (Docker)
- [ ] Kubernetes deployment manifests
- [ ] Monitoring/observability (Prometheus, Grafana)
- [ ] Load testing
- [ ] Security audit

---

## Success Criteria

### Functional
- ✅ Multi-provider LLM calls with automatic fallback
- ✅ YAML agents execute with full lifecycle management
- ✅ Autonomous coordinator heals failures without human intervention
- ✅ Quantum substrate used for provider selection and agent coordination

### Non-Functional
- ✅ P99 latency < 500ms for simple requests
- ✅ 99.9% uptime
- ✅ Auto-recovery from any single component failure
- ✅ Zero data loss in audit logs
- ✅ Horizontal scaling to 1000+ concurrent sessions

### Operational
- ✅ One-command deployment (`kubectl apply -f veilos.yaml`)
- ✅ Comprehensive metrics dashboard
- ✅ Automated testing in CI/CD
- ✅ Documentation for operators and developers

---

## File Structure

```
VEILos4/
├── orchestration/              # NEW: Orchestration layer
│   ├── gateway.py             # Gateway: routing & session
│   ├── lane_queue.py          # Lane Queue: serial execution
│   ├── agent_engine.py        # Agent Execution Engine
│   ├── autonomous_coordinator.py  # Self-extend/monitor/heal
│   ├── providers/             # Provider abstraction
│   │   ├── router.py          # Provider router with fallback
│   │   ├── base.py            # Base adapter interface
│   │   ├── openai_adapter.py
│   │   ├── anthropic_adapter.py
│   │   ├── google_adapter.py
│   │   └── ollama_adapter.py
│   └── tools/                 # Tool registry
│       ├── registry.py
│       └── [tool implementations]
├── core/                      # PRESERVED: VEIL4 Core
│   ├── quantum/               # Quantum substrate
│   ├── security/              # Capability security
│   ├── parity/                # Cognitive parity
│   ├── audit/                 # Audit logging
│   └── veil4_system.py
├── concierge_os/              # REFACTORED: Use new orchestration
│   ├── integrations/          # DEPRECATED: Replace with orchestration/providers
│   └── agent/                 # DEPRECATED: Replace with orchestration/agent_engine
├── agents/                    # PRESERVED: YAML agent definitions
├── deployment/                # NEW: Production deployment
│   ├── docker/
│   ├── kubernetes/
│   └── monitoring/
└── docs/
    ├── MODERNIZATION_ARCHITECTURE.md  # This document
    └── MIGRATION_GUIDE.md             # Step-by-step migration
```

---

## Next Steps

1. **Review and approve this architecture** with user
2. **Create detailed implementation plan** for Phase 1
3. **Set up development environment** (fix PyYAML dependency)
4. **Implement Gateway layer** as first concrete deliverable
5. **Write integration tests** for Gateway + VEIL4 Core

---

## Open Questions

1. **Deployment target**: Kubernetes required or support Docker Compose for simpler deployments?
2. **Primary use case**: What's the first real-world workload to optimize for?
3. **Model preferences**: Which providers are critical (OpenAI, Anthropic, both)?
4. **Resource constraints**: Expected scale (10s, 100s, 1000s of concurrent users)?

---

**Author**: Sisyphus (Claude Code)  
**Reviewers**: Joel Hooks (Principal)  
**Status**: AWAITING APPROVAL
