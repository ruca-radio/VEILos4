# VEILos4 Terminal Console

A modern, React-based terminal console for the VEIL4 Quantum-Cognitive Operating System. Designed to be virtualized and run by frontier LLMs.

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

#### Quantum Commands
```bash
quantum create <id>      # Create quantum superposition
quantum observe <id>     # Collapse quantum state
quantum list             # List active states
```

#### Capability Commands
```bash
capability grant <agent> <resource> <perms>  # Grant capabilities
capability verify <token>                     # Verify capability token
```

#### Agent Commands
```bash
agent register <id> <type>   # Register agent (HUMAN/MODEL)
agent list                    # List all agents
agent info <id>               # Show agent details
```

#### Plugin Commands
```bash
plugin list              # List loaded plugins
plugin load <name>       # Load a plugin
plugin unload <name>     # Unload a plugin
```

#### System Commands
```bash
status                   # Show system status
help                     # Display help
clear                    # Clear terminal
echo <message>           # Echo message
veil4 <command>          # Execute VEIL4 backend command
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

- **Quantum Operations**: Create and manipulate quantum superpositions
- **Agent Management**: Register and manage multiple agents (human or model)
- **Capability System**: Fine-grained permission management
- **Plugin System**: Extensible architecture via plugins
- **Audit Trail**: Complete transparency of all operations
- **Session Isolation**: Each terminal session is isolated
- **Real-time Feedback**: Immediate command execution results

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
