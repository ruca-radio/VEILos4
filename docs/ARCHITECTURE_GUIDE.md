# VEILos4 Architecture Guide

## System Overview

VEILos4 is a layered operating system that runs between the surface layer (user interfaces) and the cognitive layer (large language models). It provides primitives for quantum state management, capability-based security, extensibility, and self-modification.

```
┌─────────────────────────────────────────────────────────┐
│                  SURFACE LAYER                          │
│  ┌──────┐  ┌───────┐  ┌─────┐  ┌──────────────────┐   │
│  │ TUI  │  │ Shell │  │ Web │  │ Programmatic API │   │
│  └──┬───┘  └───┬───┘  └──┬──┘  └────────┬─────────┘   │
└─────┼──────────┼─────────┼──────────────┼──────────────┘
      │          │         │              │
      └──────────┴─────────┴──────────────┘
                        │
              ┌─────────▼─────────┐
              │   VEIL KERNEL     │
              │   veil_kernel.py  │
              └─────────┬─────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
   ┌────▼────┐   ┌──────▼──────┐  ┌────▼──────┐
   │  VEIL4  │   │  Cognitive  │  │ Scaffold  │
   │  Core   │   │   Stack     │  │  Engine   │
   └────┬────┘   └─────────────┘  └───────────┘
        │
   ┌────┴──────────────────────────────────┐
   │           VEIL4 SUBSYSTEMS            │
   │  ┌──────────┐  ┌───────────────────┐  │
   │  │ Quantum  │  │ Capability        │  │
   │  │ Substrate│  │ Security          │  │
   │  ├──────────┤  ├───────────────────┤  │
   │  │ Plugin   │  │ Cognitive Parity  │  │
   │  │ System   │  │ Layer             │  │
   │  ├──────────┤  ├───────────────────┤  │
   │  │ Audit    │  │ VEILos Runtime    │  │
   │  │ Log      │  │ (token interp.)   │  │
   │  └──────────┘  └───────────────────┘  │
   └───────────────────────────────────────┘
                        │
              ┌─────────▼─────────┐
              │  COGNITIVE LAYER  │
              │  (LLM Providers)  │
              └───────────────────┘
```

## Component Details

### 1. VEIL Kernel (`veil_kernel.py`)

The unified entry point. All interfaces route through this single file.

**Responsibilities:**
- Intent parsing (natural language → structured commands)
- Routing (dispatches to correct subsystem)
- Execution (runs operations, returns results)
- State management (tracks execution history)

**Key Classes:**
- `IntentParser` — Recognizes 13 intent types from natural language
- `VEILKernel` — Main orchestrator with `execute()` API

**Intent Types:**

| Type | Trigger | Handler |
|---|---|---|
| `create_quantum` | "create quantum", "superposition" | Creates quantum state |
| `observe_state` | "observe" + "state" | Collapses superposition |
| `grant_capability` | "grant" + "capability" | Issues security token |
| `register_agent` | "register" + "agent" | Registers agent |
| `list_agents` | "list" + "agent" | Lists agents |
| `load_module` | "load" + "module" | Loads extension |
| `scaffold` | "scaffold", "build me", "create a" | Self-modification |
| `think` | "think", "reason", "analyze" | Cognitive processing |
| `stack_info` | "stack" + "info/status/layers" | Stack status |
| `templates` | "template" + "list/show" | List scaffold templates |
| `status` | "status", "info" | System status |
| `help` | "help" | Help text |
| `veilos_command` | (fallthrough) | VEILos token interpreter |

### 2. VEIL4 Core System (`core/veil4_system.py`)

The quantum-cognitive operating system. Manages:
- Quantum state superposition and collapse
- Capability-based security (grant, verify, revoke)
- Agent registration and parity
- Plugin loading and management
- Immutable audit logging

**Key Subsystems (in `core/`):**

| Directory | Purpose |
|---|---|
| `core/quantum/` | Quantum substrate — superposition, coherence, observation |
| `core/security/` | Capability security — tokens, verification, delegation |
| `core/extensibility/` | Plugin framework — loading, hooks, lifecycle |
| `core/parity/` | Cognitive parity — unified interface for humans and models |
| `core/audit/` | Immutable audit log — all state transitions recorded |

### 3. Cognitive Stack (`core/providers/cognitive_stack.py`)

Multi-model cognitive substrate. Not message-passing agents — simultaneous co-processors in shared decision space.

**Architecture:**

```
Prompt → [Layer 1: Reasoning] ─┐
       → [Layer 2: Creative ] ─┤── Superposition → Consensus
       → [Layer 3: Analysis ] ─┘
```

Each `ModelLayer` has:
- `model_name` — Identifier (e.g., "claude-3", "qwen-72b")
- `provider` — Backend (e.g., "anthropic", "ollama", "mock")
- `specialization` — One of: REASONING, MATH, CREATIVE, ANALYSIS, GENERAL
- `priority` — Weight in consensus (higher = more influence)
- `enabled` — Can be toggled without removal

**Consensus mechanism:** Confidence-weighted averaging across all layer responses. Returns:
- `consensus` — Final answer
- `confidence` — Score [0.0, 1.0]
- `layer_responses` — Individual layer outputs

Currently uses mock responses. Production will route through `concierge_os/integrations/llm_client.py`.

### 4. Scaffold Engine (`core/modification/scaffold_engine.py`)

Self-modification system. Generates, validates, and integrates new code.

**5-Phase Pipeline:**

```
Intent → [PLANNING] → [GENERATION] → [VALIDATION] → [INTEGRATION] → [VERIFICATION]
              │              │              │              │              │
              │              │        Security scan   Wire imports   Verify works
              │         Use template     Syntax check  Update __init__
           Analyze intent                              Register
```

**Templates:**
- `provider` — LLM provider integration (generates `core/providers/{name}.py`)
- `plugin` — VEIL4 extension plugin (generates `plugins/{name}_plugin.py`)
- `module` — General module (generates `core/{name}.py`)

**Safety Features:**
- File collision detection (won't overwrite without `--force`)
- Security scanning (blocks dangerous patterns like `eval()`, `exec()`, `subprocess`)
- Rollback support (stores state before modification)
- Audit trail integration

### 5. VEILos Runtime (`veil_core.py`)

Token-interpreted runtime kernel. Handles:
- Token parsing and interpretation
- Session management
- Command routing for non-VEIL4 operations

### 6. Interface Layer

#### TUI (`interfaces/tui.py`)

Textual-based terminal interface. Components:
- `StatusPanel` — Live kernel status (Rich Text rendering)
- `CommandLog` — RichLog widget with markup support
- `VEILosTUI` — Main app, routes input to `VEILKernel.execute()`

All interfaces are thin wrappers around `VEILKernel` — the kernel is the single source of truth.

## Data Flow

### Command Execution

```
1. User types: "create quantum state with red, blue, green"
2. IntentParser.parse() → {type: "create_quantum", intent: ...}
3. VEILKernel.execute() → routes to _handle_create_quantum()
4. VEIL4.create_quantum_state() → creates superposition
5. Result returned: {status: "success", data: {state_id: ..., states: [...]}}  
6. Interface displays result
```

### Self-Scaffolding

```
1. User types: "scaffold a redis provider"
2. IntentParser.parse() → {type: "scaffold", intent: ...}
3. VEILKernel.execute() → routes to _handle_scaffold()
4. ScaffoldEngine.scaffold(intent) → 5-phase pipeline:
   a. PLANNING: Detect template="provider", name="redis"
   b. GENERATION: Apply provider template → generate code
   c. VALIDATION: Security scan + syntax check
   d. INTEGRATION: Write file, update imports
   e. VERIFICATION: Confirm file exists and imports
5. ScaffoldResult returned with success/failure + artifacts
```

### Cognitive Processing

```
1. User types: "think about optimization strategies"
2. IntentParser.parse() → {type: "think", intent: ...}
3. VEILKernel.execute() → routes to _handle_think()
4. CognitiveStack.process_prompt(prompt):
   a. All layers process simultaneously
   b. Responses collected in superposition
   c. Consensus computed via confidence weighting
5. Result: {consensus, confidence, layer_responses}
```

## Security Model

VEILos4 uses object-capability security:

- **Capabilities are unforgeable tokens** — you can't guess them
- **Least privilege** — agents get only what they need
- **Delegation** — capabilities can be passed but not escalated
- **Revocation** — capabilities expire or can be revoked
- **Audit** — every grant, check, and revocation is logged immutably

The scaffold engine adds another security layer: generated code is scanned for dangerous patterns before integration.

## Extension Points

1. **New intent types** — Add patterns to `IntentParser.parse()` and handlers to `VEILKernel`
2. **New model layers** — `cognitive_stack.add_layer(ModelLayer(...))` with any provider
3. **New scaffold templates** — Add to `ScaffoldEngine.templates`
4. **New plugins** — Via VEIL4's extensibility framework
5. **New interfaces** — Wrap `VEILKernel` (shell, web, API, etc.)

## File Map

```
VEILos4/
├── veil_kernel.py                    # Unified kernel (entry point)
├── veil_core.py                      # VEILos token runtime
├── interfaces/
│   └── tui.py                        # Textual TUI
├── core/
│   ├── veil4_system.py               # VEIL4 main system
│   ├── quantum/                      # Quantum substrate
│   │   ├── superposition.py
│   │   └── coherence.py
│   ├── security/                     # Capability security
│   │   └── capabilities.py
│   ├── extensibility/                # Plugin framework
│   │   └── plugin_manager.py
│   ├── parity/                       # Cognitive parity
│   │   └── unified_interface.py
│   ├── audit/                        # Immutable audit log
│   │   └── immutable_log.py
│   ├── providers/
│   │   ├── cognitive_stack.py        # Multi-model cognitive substrate
│   │   └── openai.py                # OpenAI provider (existing)
│   └── modification/
│       └── scaffold_engine.py        # Self-modification engine
├── tests/                            # 51 tests, all passing
├── docs/
│   ├── USER_GUIDE.md
│   └── ARCHITECTURE_GUIDE.md
└── demo.py                           # End-to-end demonstration
```