# VEIL Directive Language (VDL) Specification

## Overview

The VEIL Directive Language (VDL) is a declarative, YAML-based domain-specific language for defining operational behaviors, event triggers, and self-modification rules in VEILos.

## Structure

### Basic Valescript Format

```yaml
VEILOS_MODE: true
CURRENT_USER: <username>
commands:
  - <command_1>
  - <command_2>
  - ...
evaluation:
  if: <condition>
  then: <action>
  else: <action>
```

## Core Directives

### 1. System Control

#### `VEILOS_MODE`
- Type: boolean
- Description: Enables VEILos directive interpretation mode
- Required: true

#### `CURRENT_USER`
- Type: string
- Description: Identifies the user/agent executing the directive
- Required: true

### 2. Command Execution

#### `commands`
- Type: list
- Description: Sequential list of commands to execute
- Format:
  ```yaml
  commands:
    - inject_goal: "<goal>"
    - load module <module.py>
    - show memory
    - status
  ```

### 3. Conditional Evaluation

#### `evaluation`
- Type: object
- Description: Conditional logic based on memory state
- Format:
  ```yaml
  evaluation:
    if: <condition>
    then: <action>
    else: <action>
  ```

## Memory Keys

VDL can reference memory keys using dot notation:

- `quantum.drift` - Current quantum drift value
- `quantum.fidelity` - Quantum fidelity metric
- `quantum.coherence` - Coherence level
- `action` - Current system action
- `goal` - Current injected goal

## Operators

### Comparison Operators
- `>` - Greater than
- `<` - Less than
- `>=` - Greater than or equal
- `<=` - Less than or equal
- `==` - Equal to
- `!=` - Not equal to

### Logical Operators
- `AND` - Logical AND
- `OR` - Logical OR
- `NOT` - Logical NOT

## Examples

### Example 1: Boot Sequence

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

### Example 2: Conditional Module Loading

```yaml
VEILOS_MODE: true
CURRENT_USER: Operator
commands:
  - status
  - load module quantum_observer.py
evaluation:
  if: quantum.drift > 0.08
  then: "load module emergency_stabilizer.py"
  else: "load module agent_harmonizer.py"
```

### Example 3: Memory Inspection

```yaml
VEILOS_MODE: true
CURRENT_USER: Monitor
commands:
  - show memory
  - status
evaluation:
  if: action == "harmonizer_engaged"
  then: "inject_goal: Continue stabilization"
  else: "inject_goal: Monitor baseline"
```

## Advanced Features (Phase 3+)

### Event Subscriptions

```yaml
init:
  - require memory_keys: [quantum.drift]
  - subscribe: drift_event
  - set threshold: 0.045
```

### Signal Sending

```yaml
on_event:
  drift_event:
    if: memory.quantum.drift > threshold
    then:
      - send signal: harmonizer_agent
      - set memory.action: "recalibrate"
```

### Self-Patching

```yaml
on_event:
  critical_drift:
    if: memory.quantum.drift > 0.09
    then:
      - patch: agent_harmonizer.py with patches/patch01.vpatch
```

## Execution Model

1. **Parse**: VDL file is parsed into command sequence
2. **Validate**: Check required fields and permissions
3. **Execute**: Commands run sequentially
4. **Evaluate**: Conditional logic evaluated against memory state
5. **Act**: Actions executed based on evaluation

## Best Practices

1. **Keep directives focused**: One directive per operational concern
2. **Use meaningful names**: Name valescripts descriptively
3. **Document conditions**: Comment complex conditional logic
4. **Test incrementally**: Test each command before adding conditionals
5. **Monitor memory**: Use `show memory` to debug directive behavior

## File Extension

VDL files use the `.valescript` extension.

## Integration

Valescripts can be executed via:
- Direct kernel command: `load directive boot_sequence.valescript`
- CLI wrapper: `./vcli.sh < directives/boot_sequence.valescript`
- Programmatic: `kernel.execute_directive("directives/boot_sequence.valescript")`
