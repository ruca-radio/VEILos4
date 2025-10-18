# VEILos4 Terminal Console

A modern, React-based **dual-mode terminal console** for the VEIL4 Quantum-Cognitive Operating System. Designed to be virtualized and run by frontier LLMs.

## Dual Terminal Modes

The terminal operates in **two integrated modes**:

### 1. VEILos4 Mode
Execute quantum-cognitive system commands:
- **Quantum Operations**: Create and observe quantum superpositions
- **Agent Management**: Register and manage human/AI agents
- **Capability System**: Fine-grained permission control
- **Plugin System**: Load and manage extensibility plugins
- **System Status**: Monitor VEILos4 system state

### 2. Linux Shell Mode
Execute standard Linux shell commands:
- **File Operations**: ls, cat, grep, find, mkdir, touch, rm, cp, mv
- **Navigation**: cd, pwd (with state persistence)
- **Process Management**: ps, top, kill
- **System Information**: df, du, free, uname
- **Development Tools**: git, python, node, npm, pip
- **Environment**: export variables, shell configuration

**Automatic Command Detection**: The terminal automatically detects whether a command is VEILos4 or Linux and routes it appropriately. Use `linux <cmd>` for explicit shell execution.

## Features

### Bootloader Sequence
- **Splash Screen**: Animated VEILos4 logo with quantum-inspired effects
- **Settings Configuration**: Comprehensive boot settings panel
- **Loading Animation**: Smooth progress bar during initialization
- **System Ready**: Seamless transition to terminal

### Boot Settings
- **User Mode**: User or Sudo privileges
- **Network**: Enable/disable network connectivity
- **Plugin Manager**: Control plugin system
- **Multi-model Support**: Enable multiple AI models
- **Mix Model**: Combine different model capabilities
- **Agentic Mode**: Enable autonomous agent behavior
- **Memory Persistence**: Persistent state across sessions
- **PostgreSQL DSN**: Database connection configuration
- **Provider Configuration**: Configure up to 5 AI model providers
- **VOS File Upload**: Load VEILos configuration files
- **Launch URL**: Specify startup script URL

### Terminal Features
- **Command Execution**: Full VEIL4 command support
- **Command History**: Navigate with arrow keys
- **Syntax Highlighting**: Color-coded output by type
- **Auto-scroll**: Automatic scrolling to latest output
- **VEIL4 Backend Integration**: Real-time communication with Python backend

### Supported Commands

#### VEILos4 Commands (Quantum-Cognitive Operations)
```bash
quantum create <id>      # Create quantum superposition
quantum observe <id>     # Collapse quantum state
quantum list             # List active states
```

```bash
capability grant <agent> <resource> <perms>  # Grant capabilities
capability verify <token>                     # Verify capability token
```

```bash
agent register <id> <type>   # Register agent (HUMAN/MODEL)
agent list                    # List all agents
agent info <id>               # Show agent details
```

```bash
plugin list              # List loaded plugins
plugin load <name>       # Load a plugin
plugin unload <name>     # Unload a plugin
```

```bash
status                   # Show system status
help                     # Display help
```

#### Linux Shell Commands (Auto-Detected)
```bash
# File operations
ls [-la] [path]          # List directory contents
cat <file>               # Display file contents
grep <pattern> <file>    # Search for pattern
find <path> -name <pattern>  # Find files
mkdir <dir>              # Create directory
touch <file>             # Create empty file
rm <file>                # Remove file
cp <src> <dst>           # Copy file
mv <src> <dst>           # Move/rename file

# Navigation
cd <directory>           # Change directory (state persists!)
pwd                      # Print working directory

# Process management
ps [aux]                 # List processes
top                      # Display process monitor
kill <pid>               # Terminate process

# System information
df [-h]                  # Disk space usage
du [-sh] <path>          # Directory size
free [-h]                # Memory usage
uname [-a]               # System information

# Development tools
git <command>            # Git version control
python <script>          # Run Python script
node <script>            # Run Node.js script
npm <command>            # Node package manager
pip <command>            # Python package manager

# Environment
export VAR=value         # Set environment variable (persists in session!)
echo $VAR                # Display variable value

# Shell control
shell info               # Show shell information
shell env                # List environment variables
```

#### Explicit Linux Commands
```bash
linux <command>          # Force execution as Linux shell command
```

#### Terminal Control
```bash
clear                    # Clear terminal
```

## Installation

### Frontend (React)

```bash
cd surface/terminal
npm install
npm run dev
```

The terminal will be available at `http://localhost:5173`

### Backend (Python)

```bash
# From repository root
pip install -r requirements.txt
pip install flask flask-cors

# Run the API server
python surface/terminal/api_server.py
```

The API server will run on `http://localhost:5000`

## Architecture

```
┌──────────────────────────────────────┐
│   React Terminal Console (Frontend)  │
│   - VeilosTerminalConsole.tsx        │
│   - Bootloader & Settings UI         │
│   - Command Input & Display          │
└─────────────┬────────────────────────┘
              │ HTTP/REST API
              ▼
┌──────────────────────────────────────┐
│   Flask API Server (Middleware)      │
│   - api_server.py                    │
│   - REST endpoints                   │
│   - Session management               │
└─────────────┬────────────────────────┘
              │ Python API
              ▼
┌──────────────────────────────────────┐
│   Terminal Backend (Integration)     │
│   - terminal_backend.py              │
│   - Command parsing & execution      │
└─────────────┬────────────────────────┘
              │ VEIL4 API
              ▼
┌──────────────────────────────────────┐
│   VEIL4 Core System                  │
│   - Quantum Substrate                │
│   - Capability Security              │
│   - Extensibility Framework          │
│   - Cognitive Parity                 │
│   - Audit Transparency               │
└──────────────────────────────────────┘
```

## Usage

### Basic Usage

1. Start the terminal console:
   ```bash
   npm run dev
   ```

2. Configure boot settings in the settings panel
3. Click "Boot System"
4. Execute commands in the terminal

### With VEIL4 Backend

1. Start the VEIL4 API server:
   ```bash
   python surface/terminal/api_server.py
   ```

2. Start the terminal frontend:
   ```bash
   npm run dev
   ```

3. The terminal will automatically connect to the backend

### Example Session

```bash
$ help
VEILos4 Terminal Commands:
...

$ agent register alice HUMAN
✓ Agent 'alice' registered as HUMAN

$ quantum create state_001
✓ Quantum state 'state_001' created with 2 superposed states

$ quantum observe state_001
✓ Quantum state collapsed to: {"choice": "A", "probability": 0.5}

$ status
System Status:
...
```

## Virtualization for LLMs

The terminal is designed to be accessible to frontier LLMs through:

1. **API-First Design**: All operations available via REST API
2. **JSON Communication**: Structured input/output
3. **Stateful Sessions**: Session-based interaction model
4. **Command Documentation**: Built-in help system
5. **Error Handling**: Clear error messages and recovery

### LLM Integration Example

```python
import requests

# Create session
session = requests.post('http://localhost:5000/api/veil4/session', 
    json={'bootSettings': {...}})
session_id = session.json()['session']['session_id']

# Execute command
result = requests.post('http://localhost:5000/api/veil4/execute',
    json={'sessionId': session_id, 'command': 'quantum create state_001'})
print(result.json()['output'])
```

## Development

### File Structure

```
surface/terminal/
├── VeilosTerminalConsole.tsx  # Main React component
├── terminal_backend.py         # Python backend integration
├── api_server.py               # Flask API server
├── App.tsx                     # React entry point
├── index.html                  # HTML template
├── package.json                # Node dependencies
├── tsconfig.json               # TypeScript config
├── vite.config.ts              # Vite config
└── README.md                   # This file
```

### Building for Production

```bash
npm run build
```

The production build will be in the `dist/` directory.

## Features for Frontier LLMs

The dual-mode terminal provides comprehensive functionality for AI models:

### VEILos4 Operations
- **Quantum Operations**: Create and manipulate quantum superpositions for decision-making
- **Agent Management**: Register and manage multiple agents (human or model)
- **Capability System**: Fine-grained permission management
- **Plugin System**: Extensible architecture via plugins
- **Audit Trail**: Complete transparency of all operations

### Linux Shell Access
- **File System Access**: Read, write, navigate the file system
- **Process Control**: Monitor and manage system processes
- **System Information**: Query system resources and status
- **Development Tools**: Execute scripts, run commands, use version control
- **Environment Control**: Set variables, configure shell state

### Integration Features
- **Session Isolation**: Each terminal session is isolated with its own state
- **State Persistence**: Working directory and environment variables persist across commands
- **Security Controls**: Capability-based access control prevents unauthorized operations
- **Automatic Routing**: Commands are automatically routed to appropriate handler
- **Real-time Feedback**: Immediate command execution results
- **Comprehensive API**: All functionality available via REST endpoints

### AI Model Usage Patterns

#### Pattern 1: Information Gathering
```bash
# Register as AI agent
agent register claude_instance MODEL

# Explore file system
ls /data
cat /data/config.json

# Check system resources
df -h
free -h

# View status
status
```

#### Pattern 2: Quantum Decision Making
```bash
# Create quantum state for decision
quantum create decision_001

# Analyze options (AI model processing)
# ...

# Observe and get result
quantum observe decision_001
```

#### Pattern 3: Development Workflow
```bash
# Navigate to project
cd /home/project

# Check version control
git status
git log --oneline -5

# Run tests
python -m pytest tests/

# Create quantum state for result analysis
quantum create test_results
```

#### Pattern 4: Mixed Operations
```bash
# Combine VEILos4 and Linux operations
agent register ai_processor MODEL
cd /data/processing
ls *.json
capability grant ai_processor /data/processing read,write
quantum create processing_state
python process_data.py
quantum observe processing_state
```

## Design Philosophy

The VEILos4 Terminal Console implements:

1. **Cognitive Parity**: Same interface for humans and AI models
2. **Quantum-Inspired**: Operations can exist in superposition
3. **Security-First**: Capability-based access control
4. **Extensible**: Plugin architecture at every layer
5. **Transparent**: Complete audit trail of operations

## License

See the repository LICENSE file for details.

## Contributing

Contributions are welcome! Please ensure:
- Code follows TypeScript/React best practices
- Commands integrate with VEIL4 backend
- Documentation is updated
- Tests are added for new features
