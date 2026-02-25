# VEILos4 API Reference

Complete API documentation for VEILos4 components.

---

## Table of Contents

- [VEILKernel](#veilkernel)
- [CognitiveStack](#cognitivestack)
- [ScaffoldEngine](#scaffoldengine)
- [IntentParser](#intentparser)
- [Interfaces](#interfaces)
  - [TUI](#tui)
  - [Shell](#shell)
  - [Web](#web)

---

## VEILKernel

Main entry point for VEILos4 system. Manages subsystems, processes natural language commands, and coordinates all operations.

### Constructor

```python
VEILKernel(config: Optional[Dict[str, Any]] = None)
```

**Parameters:**
- `config` (dict, optional): Kernel configuration
  - `debug` (bool): Enable debug logging (default: False)
  - `cognitive_layers` (int): Number of cognitive layers (default: 3)
  - `audit_enabled` (bool): Enable audit logging (default: True)

**Returns:** VEILKernel instance

**Example:**
```python
kernel = VEILKernel(config={'debug': True, 'cognitive_layers': 5})
```

---

### Methods

#### `start()`

Initialize all subsystems and cognitive stack.

**Returns:** dict
- `status` (str): 'success' or 'error'
- `subsystems` (list): List of initialized subsystem names
- `cognitive_layers` (int): Number of active cognitive layers
- `message` (str): Status message

**Example:**
```python
result = kernel.start()
# {'status': 'success', 'subsystems': ['quantum', 'security', ...], 'cognitive_layers': 3}
```

**Raises:**
- `RuntimeError`: If initialization fails

---

#### `execute(command: str, context: Optional[Dict] = None)`

Execute natural language command through intent parser.

**Parameters:**
- `command` (str): Natural language command
- `context` (dict, optional): Additional execution context

**Returns:** dict
- `status` (str): 'success' or 'error'
- `intent_type` (str): Detected intent type
- `message` (str): Execution result message
- `data` (dict, optional): Result data (varies by intent type)

**Supported Intent Types:**
- `query` — Information retrieval
- `quantum_create` — Create quantum state
- `quantum_observe` — Collapse quantum state
- `quantum_entangle` — Entangle two states
- `memory_store` — Store memory
- `memory_retrieve` — Retrieve memory
- `cognitive_process` — Multi-model reasoning
- `security_grant` — Grant capability
- `security_revoke` — Revoke capability
- `security_check` — Check capability
- `scaffold` — Self-modify/create component
- `audit_query` — Query audit log
- `system_status` — Get system status

**Example:**
```python
# Query intent
result = kernel.execute("What is the current system status?")
# {'status': 'success', 'intent_type': 'query', 'message': 'System operational', ...}

# Quantum intent
result = kernel.execute("Create quantum state named coherent_state")
# {'status': 'success', 'intent_type': 'quantum_create', 'state_id': 'coherent_state', ...}

# Cognitive intent
result = kernel.execute("Analyze the implications of quantum computing")
# {'status': 'success', 'intent_type': 'cognitive_process', 'consensus': '...', 'confidence': 0.85}
```

**Raises:**
- `ValueError`: If command is invalid or empty
- `RuntimeError`: If execution fails

---

#### `shutdown()`

Gracefully shutdown all subsystems.

**Returns:** dict
- `status` (str): 'success' or 'error'
- `message` (str): Shutdown status message

**Example:**
```python
result = kernel.shutdown()
# {'status': 'success', 'message': 'VEILKernel shutdown complete'}
```

---

## CognitiveStack

Multi-model consensus engine with quantum superposition. Coordinates multiple LLMs to produce high-confidence responses.

### Constructor

```python
CognitiveStack(config: Optional[Dict[str, Any]] = None)
```

**Parameters:**
- `config` (dict, optional): Stack configuration
  - `min_confidence` (float): Minimum consensus confidence (default: 0.7)
  - `coherence_threshold` (float): Quantum coherence threshold (default: 0.8)

**Returns:** CognitiveStack instance

---

### Methods

#### `add_layer(layer: ModelLayer)`

Add model layer to cognitive stack.

**Parameters:**
- `layer` (ModelLayer): Model layer to add

**Returns:** None

**Example:**
```python
from core.providers.cognitive_stack import ModelLayer, ModelSpecialization

stack = CognitiveStack()
stack.add_layer(ModelLayer(
    model_name='claude-3',
    provider='anthropic',
    specialization=ModelSpecialization.REASONING,
    priority=1
))
```

---

#### `process_prompt(prompt: str, context: Optional[Dict] = None)`

Process prompt through all cognitive layers and return consensus.

**Parameters:**
- `prompt` (str): Input prompt
- `context` (dict, optional): Additional context

**Returns:** dict
- `consensus` (str): Consensus response from all layers
- `confidence` (float): Confidence score (0.0 to 1.0)
- `layer_responses` (list): Individual layer responses
  - `layer` (str): Layer name
  - `response` (str): Layer response
  - `weight` (float): Layer weight/priority

**LLM Provider Support:**
- **Ollama**: Set `OLLAMA_BASE_URL` environment variable
- **OpenAI**: Set `OPENAI_API_KEY` environment variable
- **Anthropic**: Set `ANTHROPIC_API_KEY` environment variable
- **xAI**: Set `XAI_API_KEY` environment variable
- **Fallback**: Uses mock responses if no API keys configured

**Example:**
```python
result = stack.process_prompt("What are the implications of quantum entanglement?")
# {
#   'consensus': 'Quantum entanglement implies non-local correlations...',
#   'confidence': 0.85,
#   'layer_responses': [
#     {'layer': 'claude-3', 'response': '...', 'weight': 1.0},
#     {'layer': 'gpt-4', 'response': '...', 'weight': 0.8}
#   ]
# }
```

---

#### `get_coherence()`

Get quantum coherence of cognitive stack.

**Returns:** float
- Coherence value between 0.0 (decoherent) and 1.0 (fully coherent)

**Example:**
```python
coherence = stack.get_coherence()  # 0.92
```

---

## ModelLayer

Represents a single LLM layer in the cognitive stack.

### Constructor

```python
ModelLayer(
    model_name: str,
    provider: str,
    specialization: ModelSpecialization,
    priority: int = 1
)
```

**Parameters:**
- `model_name` (str): Model identifier (e.g., 'claude-3', 'gpt-4')
- `provider` (str): Provider name ('anthropic', 'openai', 'ollama', 'xai')
- `specialization` (ModelSpecialization): Model specialization
  - `REASONING` — Logical reasoning
  - `MATH` — Mathematical computation
  - `CREATIVE` — Creative writing
  - `ANALYSIS` — Data analysis
  - `GENERAL` — General purpose
- `priority` (int): Layer priority (higher = more weight, default: 1)

**Example:**
```python
layer = ModelLayer(
    model_name='claude-3-opus',
    provider='anthropic',
    specialization=ModelSpecialization.REASONING,
    priority=2
)
```

---

## ScaffoldEngine

Self-modification engine for creating new components, interfaces, and plugins.

### Constructor

```python
ScaffoldEngine(kernel: VEILKernel)
```

**Parameters:**
- `kernel` (VEILKernel): Parent kernel instance

**Returns:** ScaffoldEngine instance

---

### Methods

#### `scaffold(intent: str, agent_id: str = 'system', force: bool = False)`

Scaffold new component from intent description.

**Parameters:**
- `intent` (str): Natural language description of component to create
- `agent_id` (str): Agent identifier (default: 'system')
- `force` (bool): Overwrite existing files (default: False)

**Returns:** ScaffoldResult
- `plan_id` (str): Unique plan identifier
- `phase` (str): Execution phase
- `success` (bool): Success status
- `message` (str): Status message
- `artifacts` (list): Created artifacts
  - `type` (str): Artifact type ('file', 'directory')
  - `path` (str): Artifact path
  - `size` (int, optional): File size in bytes
- `errors` (list): Error messages (if any)
- `rollback_info` (dict, optional): Rollback information

**Example:**
```python
engine = ScaffoldEngine(kernel)
result = engine.scaffold("create quantum observer plugin")
# ScaffoldResult(
#   plan_id='plan_abc123',
#   phase='complete',
#   success=True,
#   message='Plugin created successfully',
#   artifacts=[{'type': 'file', 'path': 'plugins/quantum_observer.py'}]
# )
```

**Raises:**
- `FileExistsError`: If artifact already exists and `force=False`
- `RuntimeError`: If scaffolding fails

---

#### `list_templates()`

List available scaffold templates.

**Returns:** list of dict
- `name` (str): Template name
- `description` (str): Template description
- `category` (str): Template category

**Example:**
```python
templates = engine.list_templates()
# [
#   {'name': 'plugin', 'description': 'VEIL4 plugin', 'category': 'extensibility'},
#   {'name': 'interface', 'description': 'User interface', 'category': 'interface'},
#   {'name': 'provider', 'description': 'Model provider', 'category': 'cognitive'}
# ]
```

---

## IntentParser

Natural language intent parser. Extracts intent type and parameters from commands.

### Methods

#### `parse(command: str)`

Parse natural language command into structured intent.

**Parameters:**
- `command` (str): Natural language command

**Returns:** dict
- `intent_type` (str): Detected intent type
- `confidence` (float): Detection confidence (0.0 to 1.0)
- `params` (dict): Extracted parameters (varies by intent type)

**Intent Types & Patterns:**

| Intent Type | Patterns | Params |
|-------------|----------|--------|
| `query` | "what", "how", "explain", "tell me" | `query` (str) |
| `quantum_create` | "create state", "initialize quantum" | `state_id` (str, optional) |
| `quantum_observe` | "observe state", "collapse", "measure" | `state_id` (str) |
| `quantum_entangle` | "entangle", "correlate states" | `state_a` (str), `state_b` (str) |
| `memory_store` | "remember", "store", "save" | `key` (str), `value` (str) |
| `memory_retrieve` | "recall", "retrieve", "what did" | `key` (str) |
| `cognitive_process` | "analyze", "think about", "reason" | `prompt` (str) |
| `security_grant` | "grant", "give permission", "allow" | `principal` (str), `capability` (str) |
| `security_revoke` | "revoke", "remove permission", "deny" | `principal` (str), `capability` (str) |
| `security_check` | "can I", "do I have permission", "check access" | `principal` (str), `capability` (str) |
| `scaffold` | "create", "scaffold", "build", "generate" | `intent` (str) |
| `audit_query` | "show audit", "audit log", "what happened" | `filters` (dict, optional) |
| `system_status` | "status", "health", "diagnostic" | — |

**Example:**
```python
from veil_kernel import IntentParser

parser = IntentParser()
result = parser.parse("Create quantum state named coherent_state")
# {
#   'intent_type': 'quantum_create',
#   'confidence': 0.95,
#   'params': {'state_id': 'coherent_state'}
# }
```

---

## Interfaces

### TUI

Textual-based terminal user interface.

#### Launch

```bash
python interfaces/tui.py
```

#### Features
- Real-time command execution
- Quantum state visualization
- Memory browser
- Audit log viewer
- System status dashboard

#### Keybindings
- `Ctrl+C` — Exit
- `Ctrl+L` — Clear screen
- `Up/Down` — Command history

---

### Shell

Readline-based REPL shell.

#### Launch

```bash
python interfaces/shell.py
```

#### Commands
- Standard VEILKernel commands (natural language)
- `help` — Show help
- `status` — System status
- `exit`, `quit` — Exit shell
- `clear` — Clear screen

#### Features
- Command history (persistent)
- Tab completion
- Multi-line input support

---

### Web

FastAPI-based web dashboard with REST API.

#### Launch

```bash
uvicorn interfaces.web:app --reload --port 8001
```

Access at: http://localhost:8001

#### REST API Endpoints

##### `POST /execute`

Execute command through kernel.

**Request Body:**
```json
{
  "command": "natural language command",
  "context": {}  // optional
}
```

**Response:**
```json
{
  "status": "success",
  "intent_type": "query",
  "message": "result message",
  "data": {}  // optional
}
```

##### `GET /status`

Get system status.

**Response:**
```json
{
  "status": "operational",
  "subsystems": ["quantum", "security", ...],
  "cognitive_layers": 3,
  "uptime_seconds": 123.45
}
```

##### `GET /health`

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-02-25T04:13:27Z"
}
```

---

## Error Handling

All API methods follow consistent error handling:

**Success Response:**
```python
{
  'status': 'success',
  'message': '...',
  'data': {...}  // optional
}
```

**Error Response:**
```python
{
  'status': 'error',
  'message': 'error description',
  'error_type': 'ValueError',  // optional
  'traceback': '...'  // optional, debug mode only
}
```

**Common Exceptions:**
- `ValueError` — Invalid input parameters
- `RuntimeError` — Execution failure
- `FileExistsError` — Artifact already exists (scaffolding)
- `PermissionError` — Security capability check failed

---

## Type Definitions

### ModelSpecialization (Enum)

```python
class ModelSpecialization(Enum):
    REASONING = "reasoning"
    MATH = "math"
    CREATIVE = "creative"
    ANALYSIS = "analysis"
    GENERAL = "general"
```

### ScaffoldResult (Dataclass)

```python
@dataclass
class ScaffoldResult:
    plan_id: str
    phase: str
    success: bool
    message: str
    artifacts: List[Dict]
    errors: List[str]
    rollback_info: Optional[Dict]
```

---

## Environment Variables

### LLM Provider Configuration

```bash
# Ollama (local models)
export OLLAMA_BASE_URL="http://localhost:11434"

# OpenAI
export OPENAI_API_KEY="sk-..."

# Anthropic Claude
export ANTHROPIC_API_KEY="sk-ant-..."

# xAI Grok
export XAI_API_KEY="xai-..."
```

**Note:** If no API keys are configured, CognitiveStack falls back to mock responses.

### Kernel Configuration

```bash
# Enable debug logging
export VEIL_DEBUG=true

# Set cognitive layers
export VEIL_COGNITIVE_LAYERS=5

# Disable audit logging
export VEIL_AUDIT_ENABLED=false
```

---

## Usage Examples

### Basic Workflow

```python
from veil_kernel import VEILKernel

# Initialize kernel
kernel = VEILKernel()
kernel.start()

# Query system
result = kernel.execute("What is the system status?")
print(result['message'])

# Create quantum state
result = kernel.execute("Create quantum state named superposition")
state_id = result['data']['state_id']

# Observe state (collapse)
result = kernel.execute(f"Observe state {state_id}")
print(result['data']['value'])

# Store memory
kernel.execute("Remember that the experiment succeeded")

# Cognitive processing
result = kernel.execute("Analyze the implications of this experiment")
print(result['data']['consensus'])

# Shutdown
kernel.shutdown()
```

### Multi-Model Consensus

```python
from core.providers.cognitive_stack import CognitiveStack, ModelLayer, ModelSpecialization

# Create stack with multiple models
stack = CognitiveStack()
stack.add_layer(ModelLayer('claude-3', 'anthropic', ModelSpecialization.REASONING, priority=2))
stack.add_layer(ModelLayer('gpt-4', 'openai', ModelSpecialization.ANALYSIS, priority=1))

# Process prompt
result = stack.process_prompt("What are the ethical implications of AGI?")
print(f"Consensus: {result['consensus']}")
print(f"Confidence: {result['confidence']}")

for response in result['layer_responses']:
    print(f"\n{response['layer']}: {response['response']}")
```

### Self-Modification

```python
from veil_kernel import VEILKernel
from core.modification.scaffold_engine import ScaffoldEngine

kernel = VEILKernel()
kernel.start()

engine = ScaffoldEngine(kernel)

# List available templates
templates = engine.list_templates()
for t in templates:
    print(f"{t['name']}: {t['description']}")

# Scaffold new plugin
result = engine.scaffold("create quantum observer plugin that logs all state changes")
if result.success:
    print(f"Created: {result.artifacts}")
else:
    print(f"Errors: {result.errors}")
```

---

## Performance Considerations

### CognitiveStack
- Each layer adds ~200-500ms latency (varies by provider)
- Parallel processing: layers execute concurrently
- Recommended: 2-4 layers for optimal latency/confidence tradeoff

### Quantum Operations
- State creation: O(1)
- State observation: O(1)
- Entanglement: O(1)
- Memory operations: O(1) with in-memory store

### ScaffoldEngine
- Template rendering: ~50ms
- File I/O: ~10-100ms depending on size
- Validation: ~20ms

---

## Security

### Capability System

All operations require capability grants. Check before execution:

```python
result = kernel.execute("Can I create quantum states?")
if result['data']['granted']:
    kernel.execute("Create quantum state named secure_state")
```

### Audit Log

All operations are logged. Query with:

```python
result = kernel.execute("Show audit log for principal user_123")
events = result['data']['events']
```

### Input Validation

All user inputs are validated:
- Command length: max 10,000 characters (web interface)
- State IDs: alphanumeric + underscore only
- Memory keys: max 256 characters

---

## Troubleshooting

### Common Issues

**Issue:** `ModuleNotFoundError: No module named 'textual'`  
**Fix:** Activate virtualenv: `source .venv/bin/activate`

**Issue:** CognitiveStack returns mocks instead of real LLM responses  
**Fix:** Set environment variables for LLM providers (see Environment Variables section)

**Issue:** Web interface returns 500 error on `/execute`  
**Fix:** Check kernel initialization: `kernel.start()` must be called before `execute()`

**Issue:** Scaffold engine fails with `FileExistsError`  
**Fix:** Use `force=True` parameter: `engine.scaffold(intent, force=True)`

### Debug Mode

Enable debug logging:

```python
kernel = VEILKernel(config={'debug': True})
```

---

## Version Compatibility

- Python: 3.10+
- Textual: 8.0.0+
- FastAPI: 0.115.0+
- httpx: 0.28.1+

---

## See Also

- [User Guide](USER_GUIDE.md) — Getting started and tutorials
- [Architecture Guide](ARCHITECTURE_GUIDE.md) — System architecture
- [Contributing](CONTRIBUTING.md) — Development guidelines
- [Deployment](DEPLOYMENT.md) — Production deployment
