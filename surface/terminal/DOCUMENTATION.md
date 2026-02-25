# VEILos4 Terminal Console - Complete Documentation

## Overview

The VEILos4 Terminal Console is a modern, React-based terminal interface for the VEIL4 Quantum-Cognitive Operating System. It provides a complete surface layer for interacting with VEIL4, designed to be both human-friendly and LLM-accessible.

## Architecture

### Components

1. **Frontend (React/TypeScript)**
   - `VeilosTerminalConsole.tsx` - Main terminal component
   - `App.tsx` - Application entry point
   - `index.html` - HTML template

2. **Backend (Python)**
   - `terminal_backend.py` - Terminal integration with VEIL4
   - `api_server.py` - Flask REST API server

3. **Configuration**
   - `package.json` - Node.js dependencies
   - `tsconfig.json` - TypeScript configuration
   - `vite.config.ts` - Vite build configuration

### Data Flow

```
User Input → React Component → REST API → Terminal Backend → VEIL4 Core
                                  ↓
User Display ← React Component ← JSON Response ← Command Result
```

## Installation

### Prerequisites

- Python 3.8+
- Node.js 18+
- npm or yarn

### Backend Setup

```bash
# From repository root
cd /home/runner/work/VEILos4/VEILos4

# Install Python dependencies (optional Flask dependencies)
pip install flask flask-cors

# Set PYTHONPATH
export PYTHONPATH=/home/runner/work/VEILos4/VEILos4:$PYTHONPATH

# Run the API server
python surface/terminal/api_server.py
```

The API server will start on `http://localhost:5000`

### Frontend Setup

```bash
# Navigate to terminal directory
cd surface/terminal

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Usage

### Basic Workflow

1. **Start Backend**
   ```bash
   python surface/terminal/api_server.py
   ```

2. **Start Frontend**
   ```bash
   cd surface/terminal
   npm run dev
   ```

3. **Access Terminal**
   - Open browser to `http://localhost:5173`
   - Configure boot settings
   - Click "Boot System"
   - Use terminal commands

### Boot Settings

The terminal provides comprehensive boot configuration:

- **User Mode**: Choose between `user` (limited) or `sudo` (full access)
- **Network**: Enable/disable network connectivity
- **Plugin Manager**: Control plugin system
- **Multi-model**: Support for multiple AI models
- **Mix Model**: Combine different model capabilities
- **Agentic Mode**: Enable autonomous agent behavior
- **Memory Persistence**: Maintain state across sessions
- **PostgreSQL DSN**: Database connection (optional)
- **Launch URL**: Startup script location

### Command Reference

#### Quantum Commands

Create and manipulate quantum superpositions:

```bash
# Create a quantum superposition
quantum create <state_id>

# Observe and collapse a quantum state
quantum observe <state_id>

# List active quantum states
quantum list
```

Example:
```bash
$ quantum create my_state
✓ Quantum state 'my_state' created with 2 superposed states

$ quantum observe my_state
✓ Quantum state collapsed to: {"choice": "A", "probability": 0.5}
```

#### Agent Commands

Manage agents (human or AI):

```bash
# Register a new agent
agent register <agent_id> <HUMAN|MODEL>

# List all registered agents
agent list

# Show agent information
agent info <agent_id>
```

Example:
```bash
$ agent register alice HUMAN
✓ Agent 'alice' registered as HUMAN

$ agent register gpt4 MODEL
✓ Agent 'gpt4' registered as MODEL

$ agent list
Registered agents:
  • alice
  • gpt4
```

#### Capability Commands

Fine-grained permission management:

```bash
# Grant capability to an agent
capability grant <agent_id> <resource> <permissions>

# Verify a capability token
capability verify <agent_id> <resource> <permission> <token>
```

Example:
```bash
$ capability grant alice data/documents read,write
✓ Capability granted to alice
Token: cap_abc123...

$ capability verify alice data/documents read cap_abc123...
✓ Access granted
```

#### Plugin Commands

Manage the extensibility framework:

```bash
# List loaded plugins
plugin list

# Load a plugin
plugin load <plugin_name>

# Unload a plugin
plugin unload <plugin_name>
```

#### System Commands

```bash
# Show comprehensive system status
status

# Display help message
help

# Clear terminal screen
clear

# Echo a message
echo <message>

# Execute VEIL4 backend command
veil4 <command>
```

## Programmatic Usage

### Python API

```python
from surface.terminal.terminal_backend import TerminalBackend
from core.veil4_system import VEIL4

# Initialize
veil4 = VEIL4()
terminal = TerminalBackend(veil4)
terminal.start()

# Create session
session_info = terminal.create_session("my_session", {
    "userMode": "sudo",
    "networkEnabled": True
})

# Execute commands
result = terminal.execute_command("my_session", "quantum create test_state")
print(result["output"])

# Cleanup
terminal.close_session("my_session")
veil4.shutdown()
```

### REST API

#### Get System Status
```bash
GET /api/veil4/status
```

Response:
```json
{
  "success": true,
  "running": true,
  "data": {
    "running": true,
    "active_sessions": 2,
    "total_sessions": 5
  }
}
```

#### Create Session
```bash
POST /api/veil4/session
Content-Type: application/json

{
  "bootSettings": {
    "userMode": "sudo",
    "networkEnabled": true
  }
}
```

Response:
```json
{
  "success": true,
  "session": {
    "session_id": "uuid-here",
    "agent_id": "terminal_session_uuid_sudo",
    "status": "active"
  }
}
```

#### Execute Command
```bash
POST /api/veil4/execute
Content-Type: application/json

{
  "sessionId": "uuid-here",
  "command": "quantum create test_state"
}
```

Response:
```json
{
  "success": true,
  "output": "✓ Quantum state 'test_state' created",
  "timestamp": "2025-10-18T20:41:17.654Z"
}
```

## LLM Integration

The terminal is designed for frontier LLM access:

### Key Features for LLMs

1. **Structured API**: All operations via REST endpoints
2. **JSON Communication**: Machine-readable input/output
3. **Stateful Sessions**: Maintain context across interactions
4. **Command Documentation**: Built-in help system
5. **Error Handling**: Clear error messages

### Example LLM Integration

```python
import requests

# LLM creates a session
response = requests.post('http://localhost:5000/api/veil4/session', 
    json={'bootSettings': {'userMode': 'user'}})
session_id = response.json()['session']['session_id']

# LLM executes commands
commands = [
    "quantum create decision_state",
    "agent register llm_agent MODEL",
    "quantum observe decision_state"
]

for cmd in commands:
    result = requests.post('http://localhost:5000/api/veil4/execute',
        json={'sessionId': session_id, 'command': cmd})
    print(result.json()['output'])
```

## Testing

### Run Backend Tests

```bash
cd /home/runner/work/VEILos4/VEILos4
python -m unittest tests/test_terminal.py -v
```

### Run Core Tests

```bash
python -m unittest tests/test_core.py -v
```

### Run All Tests

```bash
python -m unittest discover tests -v
```

### Test Coverage

The test suite covers:
- ✓ Terminal backend initialization
- ✓ Session creation and management
- ✓ Command execution (quantum, agent, capability, plugin)
- ✓ Command history tracking
- ✓ User/sudo mode capabilities
- ✓ Error handling
- ✓ Backend status reporting

## Development

### Frontend Development

```bash
cd surface/terminal

# Install dependencies
npm install

# Start dev server with hot reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Backend Development

The terminal backend integrates directly with VEIL4 core:

```python
class TerminalBackend:
    def __init__(self, veil4: Optional[VEIL4] = None):
        self.veil4 = veil4 or VEIL4()
        # ... initialization
    
    def execute_command(self, session_id: str, command: str):
        # Parse and execute command
        # Integrate with VEIL4 core systems
        pass
```

### Adding New Commands

1. Add command handler in `terminal_backend.py`:
```python
def _handle_mycommand(self, agent_id: str, args: List[str]) -> str:
    # Command implementation
    return "Command output"
```

2. Register in `execute_command`:
```python
elif cmd == "mycommand":
    output = self._handle_mycommand(agent_id, args)
```

3. Add to help text in `_get_help_text()`

4. Add tests in `tests/test_terminal.py`

## Production Deployment

### Backend Deployment

Use a production WSGI server:

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 surface.terminal.api_server:app
```

### Frontend Deployment

```bash
cd surface/terminal

# Build for production
npm run build

# Deploy the dist/ directory to your web server
```

### Docker Deployment

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt
RUN pip install flask flask-cors gunicorn

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "surface.terminal.api_server:app"]
```

Build and run:
```bash
docker build -t veilos4-terminal .
docker run -p 5000:5000 veilos4-terminal
```

## Security Considerations

1. **Capability-Based Access**: All operations checked against capability tokens
2. **Session Isolation**: Each terminal session has isolated state
3. **User Mode Restrictions**: User mode has limited capabilities vs sudo
4. **Audit Trail**: All operations logged in immutable audit log
5. **CORS Configuration**: Configure CORS appropriately for production

## Troubleshooting

### Backend won't start
- Check Python version (3.8+)
- Verify dependencies installed: `pip install flask flask-cors`
- Check port 5000 is not in use

### Frontend can't connect to backend
- Verify backend is running on port 5000
- Check CORS configuration in `api_server.py`
- Verify proxy configuration in `vite.config.ts`

### Commands not executing
- Check session is active
- Verify VEIL4 system is running
- Check browser console for errors

### Tests failing
- Ensure PYTHONPATH is set correctly
- Check all dependencies installed
- Run tests with verbose flag: `python -m unittest tests/test_terminal.py -v`

## Performance

- **Command Execution**: < 10ms for most commands
- **Session Creation**: < 50ms
- **Quantum Operations**: < 5ms
- **API Response Time**: < 100ms

## Future Enhancements

Planned features:
- [ ] Tab completion for commands
- [ ] Syntax highlighting in terminal
- [ ] Command aliases
- [ ] Multi-tab terminal support
- [ ] Terminal themes
- [ ] Persistent command history
- [ ] WebSocket support for real-time updates
- [ ] Terminal recording/playback
- [ ] Integration with more VEIL4 features

## License

See repository LICENSE file.

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit a pull request

## Support

For issues or questions:
- Open an issue on GitHub
- Check existing documentation
- Review test files for examples
