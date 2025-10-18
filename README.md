# VEIL4: Quantum-Cognitive Operating System

VEIL4 is an extensible operating system that runs between the **Surface Layer** (user interface) and the **Cognitive Layer** (LLM reasoning). As a quantum installation, it provides models and specialized users alike with an even plane of existence.

## Overview

VEIL4 implements a quantum-inspired substrate that maintains operations in superposition until observed, providing:

- **Quantum Substrate**: State superposition, coherence maintenance, and observation collapse
- **Capability Security**: Fine-grained, unforgeable permission tokens with delegation
- **Extensibility Framework**: Plugin architecture at every layer
- **Cognitive Parity**: Equal capabilities for both AI models and human users
- **Audit Transparency**: Immutable logging of all state transitions

## Architecture

```
┌─────────────────────────────────────────┐
│        SURFACE LAYER (I/O)              │
│   Human UI │ API │ Canvas │ Terminal    │
└──────────────┬──────────────────────────┘
               ▼
┌─────────────────────────────────────────┐
│       VEIL4 CORE OPERATING SYSTEM       │
│  ┌───────────────────────────────────┐  │
│  │    Quantum Substrate Layer        │  │
│  ├───────────────────────────────────┤  │
│  │    Capability Security Layer      │  │
│  ├───────────────────────────────────┤  │
│  │    Extensibility Framework        │  │
│  ├───────────────────────────────────┤  │
│  │    Cognitive Parity Layer         │  │
│  ├───────────────────────────────────┤  │
│  │    Audit & Transparency Layer     │  │
│  └───────────────────────────────────┘  │
└──────────────┬──────────────────────────┘
               ▼
┌─────────────────────────────────────────┐
│      COGNITIVE LAYER (LLM)              │
│  Reasoning │ Memory │ Planning │ Learning│
└─────────────────────────────────────────┘
```

## Quick Start

### Installation

```bash
git clone https://github.com/ruca-radio/VEILos4.git
cd VEILos4
pip install -r requirements.txt
```

### Basic Usage

```python
from core.veil4_system import VEIL4
from core.parity.unified_interface import AgentType

# Initialize VEIL4
veil4 = VEIL4(config={"coherence_time": 60.0})
veil4.start()

# Register a human agent
veil4.register_agent(
    agent_id="user_001",
    agent_type=AgentType.HUMAN,
    capabilities=["read", "write"],
    metadata={"name": "Alice"}
)

# Register an AI model agent
veil4.register_agent(
    agent_id="model_gpt4",
    agent_type=AgentType.MODEL,
    capabilities=["reason", "generate"],
    metadata={"model": "gpt-4"}
)

# Create a quantum superposition
veil4.create_quantum_state(
    state_id="decision_001",
    states=[
        {"choice": "option_a", "score": 0.7},
        {"choice": "option_b", "score": 0.3}
    ]
)

# Observe the state (causes collapse)
result = veil4.observe_quantum_state("decision_001", "user_001")
print(f"Collapsed to: {result}")

# Grant capability
token = veil4.grant_capability(
    resource="data/documents",
    permissions=["read", "write"],
    agent_id="user_001",
    duration_seconds=3600
)

# Verify access
has_access = veil4.verify_access(
    agent_id="user_001",
    resource="data/documents",
    permission="read",
    capability_token=token
)

# Get system status
status = veil4.get_system_status()
print(f"System status: {status}")
```

### Terminal Console

VEILos4 includes a modern, React-based terminal console:

```bash
# Start the backend API server
pip install flask flask-cors
python surface/terminal/api_server.py

# In another terminal, start the frontend
cd surface/terminal
npm install
npm run dev
```

Access the terminal at `http://localhost:5173`. See [surface/terminal/README.md](surface/terminal/README.md) for detailed documentation.

## Core Principles

### 1. Quantum Substrate
Operations exist in superposition until observed:
- Multiple potential states coexist
- Measurement/observation causes state collapse
- Coherence maintenance prevents premature decoherence
- Entanglement between related operations

### 2. Cognitive Parity
Users and models share equivalent capabilities:
- Unified API surface for all agents
- No privileged interfaces
- Equal access to system resources
- Symmetric communication patterns

### 3. Extensibility Core
Plugin architecture at every layer:
- Hook points for custom behavior
- Dynamic module loading
- Composable capability chains
- Version-safe interfaces

### 4. Audit Transparency
All state transitions logged immutably:
- Complete provenance tracking
- Cryptographic verification
- Tamper-evident logs
- Replay capability

### 5. Capability Security
Fine-grained permission model:
- Object-capability security
- Least privilege enforcement
- Capability delegation
- Revocation support

## Project Structure

```
VEILos4/
├── core/                    # Core OS components
│   ├── quantum/            # Quantum substrate implementation
│   │   ├── superposition.py    # State superposition manager
│   │   └── coherence.py        # Coherence maintenance
│   ├── security/           # Capability security system
│   │   └── capabilities.py     # Capability tokens and management
│   ├── extensibility/      # Plugin framework
│   │   └── plugin_manager.py   # Plugin loading and hooks
│   ├── parity/             # Cognitive parity layer
│   │   └── unified_interface.py # Unified agent interface
│   ├── audit/              # Audit and transparency
│   │   └── immutable_log.py    # Immutable state log
│   └── veil4_system.py     # Main VEIL4 system
├── surface/                 # Surface layer adapters
│   └── terminal/           # Terminal console interface
│       ├── VeilosTerminalConsole.tsx  # React terminal component
│       ├── terminal_backend.py        # Python backend integration
│       ├── api_server.py              # Flask REST API server
│       └── README.md                  # Terminal documentation
├── cognitive/               # Cognitive layer adapters
├── plugins/                 # Extension plugins
├── tests/                   # Test suites
├── docs/                    # Documentation
├── examples/                # Example implementations
├── ARCHITECTURE.md         # Detailed architecture spec
└── README.md               # This file
```

## Documentation

- [Architecture Specification](ARCHITECTURE.md) - Complete system architecture
- [Examples](examples/) - Example implementations and use cases
- [Plugin Development](docs/plugins.md) - Guide to creating plugins
- [Security Model](docs/security.md) - Capability security details

## Extension Points

VEIL4 supports five types of plugins:

1. **Surface Plugins** - New I/O interfaces
2. **Security Plugins** - Custom authentication/authorization
3. **Quantum Plugins** - State management strategies
4. **Audit Plugins** - Custom logging/compliance
5. **Cognitive Plugins** - LLM integration adapters

See [Plugin Development Guide](docs/plugins.md) for details.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

See [LICENSE](LICENSE) for details.

## Citation

If you use VEIL4 in your research, please cite:

```bibtex
@software{veil4,
  title = {VEIL4: Quantum-Cognitive Operating System},
  author = {ruca-radio},
  year = {2025},
  url = {https://github.com/ruca-radio/VEILos4}
}
```