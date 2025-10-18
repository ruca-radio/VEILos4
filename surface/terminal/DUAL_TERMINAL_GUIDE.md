# Dual VEILos4 and Linux Terminal Emulator

## Overview

The VEILos4 terminal now functions as a **dual-mode terminal emulator**, providing both VEILos4-specific quantum-cognitive commands and standard Linux shell command execution. This makes it a powerful interface for AI models and users alike to interact with both the VEILos4 system and the underlying operating system.

## Features

### 1. VEILos4 Commands
Execute quantum-cognitive operations:
- **Quantum operations**: Create and observe quantum superpositions
- **Agent management**: Register and manage human and AI model agents
- **Capability system**: Grant and verify fine-grained permissions
- **Plugin system**: Load and manage extensibility plugins
- **System status**: Monitor VEILos4 system state

### 2. Linux Shell Emulation
Execute standard Linux commands:
- **File operations**: ls, cat, grep, find, mkdir, rm, cp, mv
- **Navigation**: cd, pwd
- **Process management**: ps, top, kill
- **System info**: df, du, free, uname
- **Text processing**: echo, wc, sort, uniq, diff
- **Network tools**: ping, curl, wget (if available)
- **Development tools**: git, python, node, npm, pip

### 3. Session Management
- **Working directory persistence**: cd changes persist across commands
- **Environment variables**: export variables that persist in session
- **Shell state**: Each session maintains its own shell context
- **Command history**: Full command history tracking

### 4. Security
- **Capability-based access**: Commands require appropriate capabilities
- **Dangerous command blocking**: Prevents destructive commands for non-admin users
- **Session isolation**: Each terminal session is isolated
- **Audit logging**: All commands are logged for transparency

### 5. AI Model Accessibility
- **REST API**: Full functionality exposed via HTTP endpoints
- **JSON communication**: Structured input/output for programmatic access
- **Command routing**: Automatic detection of command type
- **Stateful sessions**: Session-based interaction model

## Usage

### Basic Commands

#### VEILos4 Commands
```bash
# Quantum operations
quantum create state_001
quantum observe state_001
quantum list

# Agent management
agent register alice HUMAN
agent register gpt4 MODEL
agent list
agent info alice

# Capability management
capability grant alice /data/docs read,write
capability verify alice /data/docs read <token>

# Plugin management
plugin list
plugin load my_plugin
plugin unload my_plugin

# System
status
help
```

#### Linux Shell Commands
```bash
# File operations
ls -la
cat file.txt
grep "pattern" file.txt
find . -name "*.py"

# Navigation
cd /tmp
pwd

# Process management
ps aux
top

# System information
df -h
du -sh /home
uname -a

# Environment
export MY_VAR=value
echo $MY_VAR
```

#### Explicit Linux Prefix
For ambiguous commands or to force shell execution:
```bash
linux echo "Hello World"
linux python script.py
linux git status
```

#### Shell Management
```bash
shell info        # Show shell information
shell env         # List environment variables
```

### Command Routing

The terminal automatically detects command types:

1. **VEILos4 commands** (quantum, agent, capability, plugin, status, help) are routed to VEILos4 handlers
2. **Common Linux commands** are automatically detected and executed as shell commands
3. **Unknown commands** are attempted as Linux commands first, then show error
4. **Explicit prefix** using `linux <cmd>` forces shell execution

### Session State

Each terminal session maintains:
- **Current working directory** (cwd)
- **Environment variables** (env)
- **Shell type** (default: bash)
- **Agent identity** (for capability checks)

State persists across commands within the same session:
```bash
$ cd /tmp
Changed directory to: /tmp

$ pwd
/tmp

$ export MY_VAR=hello

$ echo $MY_VAR
hello
```

## API Integration

### Creating a Session

```python
import requests

# Create session
response = requests.post('http://localhost:5000/api/veil4/session', 
    json={'bootSettings': {
        'userMode': 'user',
        'networkEnabled': True
    }})

session = response.json()['session']
session_id = session['session_id']
```

### Executing Commands

```python
# Execute VEILos4 command
response = requests.post('http://localhost:5000/api/veil4/execute',
    json={
        'sessionId': session_id,
        'command': 'quantum create my_state'
    })

result = response.json()
print(result['output'])

# Execute Linux command
response = requests.post('http://localhost:5000/api/veil4/execute',
    json={
        'sessionId': session_id,
        'command': 'ls -la'
    })

result = response.json()
print(result['output'])
print(f"Working directory: {result['cwd']}")
```

### Explicit Linux Commands

```python
# Use explicit Linux command endpoint
response = requests.post('http://localhost:5000/api/veil4/linux',
    json={
        'sessionId': session_id,
        'command': 'echo "Hello from Linux shell"'
    })

result = response.json()
print(result['output'])
```

### Getting Shell Info

```python
response = requests.get('http://localhost:5000/api/veil4/shell/info',
    params={'sessionId': session_id})

shell_info = response.json()
print(f"Shell: {shell_info['shell']}")
print(f"Working directory: {shell_info['cwd']}")
print(f"Environment variables: {shell_info['env_count']}")
```

## AI Model Usage Patterns

### Pattern 1: Information Gathering
```python
# AI model gathers system information
commands = [
    "agent register ai_model MODEL",
    "ls /etc",
    "df -h",
    "ps aux",
    "status"
]

for cmd in commands:
    result = execute_command(session_id, cmd)
    # Process result...
```

### Pattern 2: Quantum Decision Making
```python
# AI model uses quantum states for decisions
execute_command(session_id, "quantum create decision_001")
# ... analyze options ...
result = execute_command(session_id, "quantum observe decision_001")
# Use collapsed state for decision
```

### Pattern 3: Mixed Operations
```python
# AI combines VEILos4 and Linux operations
execute_command(session_id, "cd /data")
execute_command(session_id, "ls *.json")
execute_command(session_id, "agent register data_processor MODEL")
execute_command(session_id, "capability grant data_processor /data read")
execute_command(session_id, "quantum create processing_state")
```

## Security Considerations

### Capability Requirements

Commands require specific capabilities:
- **execute**: Required for all Linux shell commands
- **admin**: Required for dangerous operations (rm -rf, mkfs, etc.)
- **read**: Required for file read operations
- **write**: Required for file write operations

### Dangerous Command Blocking

Non-admin users are blocked from executing:
- `rm -rf /`
- `mkfs`
- `dd if=`
- `chmod -R 777 /`
- Fork bombs: `:(){ :|:& };:`

### Timeouts

All shell commands have a 30-second timeout to prevent hanging.

### Session Isolation

Each terminal session is isolated:
- Separate working directory
- Separate environment variables
- Separate command history
- Separate agent identity

## Examples

### Example 1: Basic Dual Usage
```bash
$ help
VEILos4 Terminal Commands...

$ ls
file1.txt  file2.txt  directory/

$ quantum create state1
✓ Quantum state 'state1' created

$ pwd
/home/user

$ agent list
Registered agents:
  • terminal_session_abc123_user
```

### Example 2: AI Model Session
```bash
# Register as AI agent
$ agent register gpt4_instance MODEL
✓ Agent 'gpt4_instance' registered as MODEL

# Create quantum state for decision
$ quantum create decision_point
✓ Quantum state 'decision_point' created

# Gather system information
$ ls /var/log
auth.log  syslog  kern.log ...

# Check system status
$ status
VEILos4 System Status:
...

# Make decision
$ quantum observe decision_point
✓ Quantum state collapsed to: {"choice": "A"}
```

### Example 3: Development Workflow
```bash
# Navigate to project
$ cd /home/user/project

# Check git status
$ git status
On branch main...

# Create quantum state for testing
$ quantum create test_run

# Run tests
$ python -m pytest tests/

# Observe results and decide
$ quantum observe test_run

# Update agent capabilities
$ capability grant developer /home/user/project write
```

## Frontend Integration

The frontend terminal component automatically supports both command types:

```typescript
// User types command in terminal
const handleCommand = async (command: string) => {
  const response = await fetch('/api/veil4/execute', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      sessionId,
      command 
    })
  });
  
  const result = await response.json();
  
  // Display output
  addOutputLine(result.output);
  
  // Update working directory display if changed
  if (result.cwd) {
    updateCwdDisplay(result.cwd);
  }
};
```

## Troubleshooting

### Command Not Found
If a command is not recognized:
1. Check if it's a VEILos4 command with `help`
2. Try explicit prefix: `linux <command>`
3. Verify command is installed: `which <command>`

### Permission Denied
If you get permission denied:
1. Check your capabilities: `agent info <your_agent_id>`
2. Request capability grant from admin
3. Switch to sudo mode if appropriate

### Command Timeout
If a command times out:
1. Reduce command complexity
2. Use background execution if needed
3. Check if command requires user input (not supported)

## Best Practices

1. **Use appropriate command types**: VEILos4 commands for system operations, Linux commands for file/process operations
2. **Maintain session state**: Use cd and export strategically
3. **Check capabilities**: Verify permissions before executing privileged commands
4. **Handle errors**: Always check command success status
5. **Log operations**: Leverage audit trail for debugging
6. **Timeout awareness**: Keep commands under 30 seconds
7. **Security conscious**: Don't expose sensitive data in commands

## Limitations

1. **No interactive commands**: Commands requiring user input are not supported
2. **30-second timeout**: Long-running commands will be terminated
3. **No job control**: Background jobs (& suffix) are not supported in the traditional sense
4. **Limited shell features**: No pipes, redirects, or complex shell syntax in some contexts
5. **Session-local state**: State doesn't persist after session closes

## Future Enhancements

Planned improvements:
- [ ] Pipe and redirect support
- [ ] Job control (background/foreground)
- [ ] Tab completion
- [ ] Command aliases
- [ ] Shell script execution
- [ ] Interactive command support
- [ ] Longer timeout options for privileged users
- [ ] Multi-shell support (zsh, fish)

## Conclusion

The dual VEILos4 and Linux terminal emulator provides a powerful, unified interface for interacting with both quantum-cognitive operations and traditional system operations. This makes it ideal for AI models that need comprehensive system access while maintaining security and auditability.
