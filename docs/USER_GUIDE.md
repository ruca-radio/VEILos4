# VEILos4 User Guide

## What is VEILos4?

VEILos4 is a quantum-cognitive operating system that runs between you (the surface layer) and large language models (the cognitive layer). It gives you and AI models an **equal plane of existence** — the same tools, the same capabilities, the same interface.

The system is self-scaffolding: you tell it what you want in natural language, and it builds what it needs.

## Quick Start

### Prerequisites

- Python 3.11+
- pip / venv

### Installation

```bash
git clone https://github.com/ruca-radio/VEILos4.git
cd VEILos4
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Launch the TUI

```bash
python interfaces/tui.py
```

This opens the terminal interface with:
- **Status panel** — Kernel state, active layers, last command
- **Log area** — Command history and results with color-coded output
- **Input prompt** — Type natural language commands

### Use Programmatically

```python
from veil_kernel import VEILKernel

kernel = VEILKernel()
kernel.start()

# Natural language — the kernel understands intent
result = kernel.execute("show system status")
print(result)

result = kernel.execute("create quantum state with options A, B, C")
print(result)

kernel.shutdown()
```

## Commands

VEILos4 understands natural language. You don't need exact syntax — just express what you want.

### Quantum Operations

| What you say | What happens |
|---|---|
| `create quantum state with red, blue, green` | Creates a superposition with those possibilities |
| `observe state decision_001 as user_alice` | Collapses the superposition, returns result |

### Agent Management

| What you say | What happens |
|---|---|
| `register agent researcher` | Registers a new agent in the system |
| `list agents` | Shows all registered agents |

### Security

| What you say | What happens |
|---|---|
| `grant capability to read documents` | Creates a capability token |

### Cognitive Stack

| What you say | What happens |
|---|---|
| `think about quantum computing applications` | Routes through multi-model cognitive stack |
| `show stack info` | Shows active model layers and configuration |
| `list available templates` | Shows scaffold templates |

### Self-Scaffolding

| What you say | What happens |
|---|---|
| `scaffold a logging provider` | Generates provider code, validates, integrates |
| `build me a cache module` | Scaffolds a new module with safety checks |
| `create a webhook integration` | Generates integration code |

### System

| What you say | What happens |
|---|---|
| `status` | Full system status |
| `help` | Available commands |
| `load module custom_plugin.py` | Loads a module into the runtime |

### Anything Else

Commands that don't match a specific pattern are passed to the VEILos token interpreter for processing.

## Architecture (Brief)

```
You (natural language)
     ↓
[Intent Parser] → understands what you want
     ↓
[Router] → dispatches to the right subsystem
     ↓
[VEIL4 Core]      ← quantum states, security, plugins
[VEILos Runtime]  ← token interpretation, sessions
[Cognitive Stack] ← multi-model reasoning
[Scaffold Engine] ← self-modification, code generation
     ↓
Result (back to you)
```

See `docs/ARCHITECTURE_GUIDE.md` for the full architecture.

## TUI Controls

| Key | Action |
|---|---|
| `Enter` | Submit command |
| `Ctrl+L` | Clear log |
| `Ctrl+C` | Quit |
| `Ctrl+P` | Command palette |
| Type `quit` or `exit` | Quit |
| Type `clear` | Clear log |

## Self-Scaffolding

VEILos4's most powerful feature is self-scaffolding. The system can generate, validate, and integrate new code on demand.

The scaffold engine runs a 5-phase pipeline:

1. **PLANNING** — Analyzes what needs to be built
2. **GENERATION** — Creates the code from templates
3. **VALIDATION** — Checks for security issues, syntax errors
4. **INTEGRATION** — Wires the new code into the system
5. **VERIFICATION** — Confirms everything works

If anything fails, the engine can roll back to the previous state.

### Available Templates

- `provider` — New LLM provider integration
- `plugin` — VEIL4 extension plugin
- `module` — General-purpose module

### Safety

- File collision detection (won't overwrite existing files without `--force`)
- Security scanning (checks for dangerous patterns)
- Rollback support (can undo failed scaffolds)
- Audit trail (all modifications logged)

## Cognitive Stack

The cognitive stack runs multiple model layers simultaneously — not as separate agents passing messages, but as a unified cognitive substrate.

Each layer has:
- **Model** — Which LLM to use
- **Provider** — Where it runs (local, API, etc.)
- **Specialization** — What it's good at (REASONING, MATH, CREATIVE, ANALYSIS, GENERAL)
- **Priority** — Weight in consensus decisions

When you ask the system to "think", all layers process simultaneously and the stack produces a consensus result with a confidence score.

## Philosophy

VEILos4 exists to remove artificial barriers between humans and AI models. Both operate as equal participants in a shared cognitive space. The system is:

- **Self-scaffolding** — Models build what they need
- **Extensible** — Everything is a plugin
- **Transparent** — All operations are audited
- **Secure** — Capability-based access control
- **Minimal** — Small kernel, organic growth