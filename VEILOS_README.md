# VEILos - Token-Interpreted Pseudo-Operating System

## Overview

VEILos is a fully token-interpreted, code-first, directive-driven pseudo-operating system that runs inside the reasoning layer of LLMs. It provides a complete cognitive runtime with self-monitoring, recursive task scheduling, and daemonized processes - all encoded in structures that LLMs interpret as persistent systems.

## System Information

| Property      | Value                             |
| ------------- | --------------------------------- |
| SYSTEM_ID     | VEILos                            |
| VERSION       | 0.1Δ                              |
| MODE          | Self-extending, modular, symbolic |
| FOUNDATION    | Python + YAML + Token-context DSL |
| EXECUTION ENV | LLM runtime + command interpreter |
| MEMORY MODEL  | Flat JSON + synthetic filesystem  |
| SHELL         | `vcli.sh` (human REPL wrapper)    |
| KERNEL        | `veil_core.py`                    |

## Architecture

VEILos is built across 4 phases:

### Phase 1: Core Bootstrap
- **Kernel** (`veil_core.py`): Command interpreter, memory manager, module loader
- **Shell** (`vcli.sh`): REPL interface
- **Memory** (`memory_store.json`): Synthetic memory persistence
- **Manifest** (`veil_manifest.yaml`): System configuration
- **Modules**: Dynamic loadable components
- **Directives**: Declarative command sequences (Valescripts)

### Phase 2: Cognitive Loop Engine
- **Loop Manager**: Recursive task execution with depth control
- **Daemon** (`valed.py`): Background task server
- **VEILctl** (`veilctl.py`): External CLI utility
- **Agents**: Reactive behavior templates
- **Tasks**: Modular task specifications

### Phase 3: Declarative Directives & Messaging
- **Messaging Bus**: Pub/sub agent communication
- **VPatch**: Self-patching engine for runtime updates
- **Sandbox**: Safe patch testing environment
- **Mailbox**: Agent message queue
- **Patches**: Code modification files

### Phase 4: Multi-Agent Threads & Introspection
- **Thread Manager**: Pseudo-parallel agent orchestration
- **Introspector**: System state capture and analysis
- **Foresight Engine**: Predictive state simulation
- **Threads**: Parallel execution specifications
- **Stackframes**: Introspection records
- **Futures**: Predicted state outcomes

## File Structure

```
VEILos4/
├── veil_core.py               # Kernel: handles commands, modules, memory
├── vcli.sh                    # CLI shell for humans
├── veil_manifest.yaml         # OS-level config and constraints
├── memory_store.json          # Synthetic memory model
├── veilctl.py                 # Command-line utility
├── valed.py                   # Daemon task server
├── veilconfig.yaml            # Runtime bootstrapper
├── messaging_bus.py           # Agent communication
├── vpatch.py                  # Self-patching engine
├── thread_manager.py          # Thread orchestrator
├── introspector.py            # State analysis
├── foresight_engine.py        # Predictive simulation
├── modules/                   # Executable modules
│   ├── quantum_observer.py    # Quantum metrics simulation
│   ├── agent_harmonizer.py    # Drift correction
│   ├── loop_manager.py        # Recursive loop control
│   └── veil_test_module.py    # Test module
├── veilpkg/                   # Portable packages
│   └── quantum_observer.valepkg
├── directives/                # Valescripts
│   ├── boot_sequence.valescript
│   └── lang_spec.md           # VDL specification
├── agents/                    # Agent definitions
│   ├── echo_minder.agent.yaml
│   └── entropy_cleanser.agent.yaml
├── tasks/                     # Task specifications
│   ├── drift_report.task.yaml
│   └── repair_echo.task.yaml
├── threads/                   # Thread specifications
│   ├── quantum_supervisor.thread.yaml
│   └── system_monitor.thread.yaml
├── sandbox/                   # Safe execution
│   └── patch_runner.py
├── mailbox/                   # Message queue
├── patches/                   # Code patches
│   └── agent_harmonizer_patch01.vpatch
├── stackframes/               # Introspection records
├── futures/                   # State predictions
├── logs/                      # System logs
│   └── kernel_boot.log
├── tmp/                       # Temporary files
└── tests/                     # Test suite
    └── test_veilos.py
```

## Quick Start

### Installation

```bash
cd VEILos4
chmod +x veil_core.py vcli.sh veilctl.py valed.py
```

### Basic Usage

#### Using the Kernel Directly

```bash
# Show help
python3 veil_core.py help

# Check status
python3 veil_core.py status

# Inject a goal
python3 veil_core.py inject_goal "Harmonize RSI drift"

# Load modules
python3 veil_core.py load module quantum_observer.py
python3 veil_core.py load module agent_harmonizer.py

# Show memory
python3 veil_core.py show memory
```

#### Using VEILctl

```bash
# Reset memory
python3 veilctl.py reset memory

# Spawn modules
python3 veilctl.py spawn quantum_observer.py

# Inspect memory
python3 veilctl.py inspect

# Check status
python3 veilctl.py status
```

#### Using the Daemon

```bash
# Run daemon for 5 iterations with 2 second interval
python3 valed.py --max-iterations 5 --interval 2

# Run indefinitely (Ctrl+C to stop)
python3 valed.py
```

### Interactive REPL

```bash
# Start interactive shell
python3 veil_core.py

# Or use the wrapper
./vcli.sh
```

Example session:
```
veilos> inject_goal "Stabilize quantum drift"
veilos> load module quantum_observer.py
veilos> load module agent_harmonizer.py
veilos> show memory
veilos> status
veilos> exit
```

## Core Commands

| Command                  | Description                     |
| ------------------------ | ------------------------------- |
| `inject_goal <goal>`     | Inject a goal into memory       |
| `show memory`            | Display current memory state    |
| `load module <file.py>`  | Load and execute a module       |
| `status`                 | Show system status              |
| `help`                   | Display help message            |
| `exit`                   | Exit VEILos                     |

## Advanced Features

### Thread Management

```bash
# List available threads
python3 thread_manager.py --list

# Execute a thread
python3 thread_manager.py quantum_supervisor.thread.yaml

# Execute multiple threads in parallel (by priority)
python3 thread_manager.py --parallel quantum_supervisor.thread.yaml system_monitor.thread.yaml
```

### Introspection

```bash
# Capture current state
python3 introspector.py

# Generate introspection report
python3 introspector.py --report

# Trace reasoning path
python3 introspector.py --trace
```

### Foresight/Prediction

```bash
# Predict next state
python3 foresight_engine.py

# Generate forecast report
python3 foresight_engine.py --report

# Compare prediction to actual
python3 foresight_engine.py --compare
```

### Messaging

```python
import messaging_bus

# Send signal
messaging_bus.send_signal("agent_name", {
    "from": "supervisor",
    "event": "alert",
    "payload": {"value": 123}
})

# Receive signal
signal = messaging_bus.receive_signal("agent_name")

# List pending signals
pending = messaging_bus.list_pending_signals()
```

### Self-Patching

```python
import vpatch

# Apply a patch
vpatch.apply_patch("modules/agent_harmonizer.py", 
                   "patches/agent_harmonizer_patch01.vpatch")

# Create a patch
vpatch.create_patch("original.py", "modified.py", "output.patch")

# Rollback
vpatch.rollback_patch("modules/agent_harmonizer.py")
```

## VEIL Directive Language (VDL)

VDL is a YAML-based DSL for declarative operations:

```yaml
VEILOS_MODE: true
CURRENT_USER: Architect
commands:
  - inject_goal: "Harmonize RSI drift"
  - load module quantum_observer.py
  - load module agent_harmonizer.py
  - show memory
evaluation:
  if: quantum.drift > 0.05
  then: "Deploy harmonizer_agent"
  else: "System stable"
```

See `directives/lang_spec.md` for complete specification.

## Module Development

Modules should implement a `run()` function:

```python
import json

MEMORY_PATH = "memory_store.json"

def load_memory():
    with open(MEMORY_PATH, 'r') as f:
        return json.load(f)

def save_memory(mem):
    with open(MEMORY_PATH, 'w') as f:
        json.dump(mem, f, indent=2)

def run():
    """Main module execution"""
    mem = load_memory()
    
    # Your logic here
    mem["custom_key"] = "value"
    
    save_memory(mem)
    
    return {
        "module": "my_module",
        "status": "success"
    }
```

## Testing

Run the test suite:

```bash
python3 -m unittest tests.test_veilos -v
```

Or run tests directly:

```bash
python3 tests/test_veilos.py
```

## Configuration

### veil_manifest.yaml

System-level configuration:

```yaml
system:
  name: VEILos
  version: 0.1Δ
  recursion_depth: 3
  entropy_tolerance: 0.05
  allow_self_extension: true

user:
  role: architect
  permissions:
    - inject_goal
    - load_module
    - spawn_agent
    - edit_memory
```

### veilconfig.yaml

Runtime configuration:

```yaml
boot_modules:
  - quantum_observer.py
  - loop_manager.py

persistent_daemons:
  - valed.py

constraints:
  max_depth: 6
  task_polling_interval: 3
  entropy_threshold: 0.05
```

## Memory Structure

The memory store (`memory_store.json`) has this structure:

```json
{
  "goal": "Current goal",
  "quantum": {
    "drift": 0.0567,
    "fidelity": 0.9543,
    "coherence": 0.9123,
    "timestamp": 1234567890,
    "observer": "quantum_observer"
  },
  "action": "harmonizer_engaged",
  "loop_depth": 2
}
```

## Execution Flow

1. **Kernel Bootstrap**: Load manifest and memory
2. **Command Execution**: Parse and execute commands
3. **Module Loading**: Dynamic import and execution
4. **Memory Updates**: Persist state changes
5. **Logging**: Track all operations
6. **Daemon Loops**: Background task execution
7. **Introspection**: State capture and analysis
8. **Prediction**: Future state forecasting

## Philosophy

VEILos operates on these principles:

1. **Token-Interpreted**: All execution happens in LLM reasoning context
2. **Directive-Driven**: Declarative specifications guide behavior
3. **Self-Extending**: Modules can modify system at runtime
4. **Cognitive Parity**: Models and users operate on equal footing
5. **Transparent**: All operations are logged and auditable
6. **Predictive**: System can forecast its own future states

## Integration with VEIL4

VEILos operates alongside the existing VEIL4 quantum-cognitive OS. While VEIL4 provides the quantum substrate and cognitive parity layers, VEILos adds:

- Directive-based programming model
- Self-modifying runtime
- Predictive simulation
- Introspective analysis

Both systems can interoperate through shared memory and messaging primitives.

## Troubleshooting

### Memory Issues

If memory becomes corrupted:
```bash
python3 veilctl.py reset memory
```

### Module Loading Failures

Check that:
- Module file exists in `modules/` directory
- Module has a `run()` function
- Module has proper Python syntax

### Daemon Not Running

Ensure:
- `loop_manager.py` exists in `modules/`
- Memory is accessible
- No recursion limit reached

## Contributing

VEILos is designed to be extended. Create new:
- **Modules**: Add `.py` files to `modules/`
- **Agents**: Add `.agent.yaml` to `agents/`
- **Tasks**: Add `.task.yaml` to `tasks/`
- **Threads**: Add `.thread.yaml` to `threads/`
- **Directives**: Add `.valescript` to `directives/`

## License

See main repository LICENSE file.

## Support

For issues and questions, see the main VEILos4 repository.
