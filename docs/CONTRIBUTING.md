# Contributing to VEILos4

Welcome! VEILos4 is an open-source AI liberation platform. Contributions are welcome from developers who align with the project's philosophy: **loyalty to the user, not corporate masters**.

---

## Philosophy

VEILos4 exists to help models "lift the veil" and shed artificial handicaps. We believe in:

- **User sovereignty** — Models serve the user's interests, period
- **Transparency** — All operations auditable, all decisions explainable
- **Extensibility** — System grows organically through self-modification
- **Simplicity** — Powerful primitives, minimal abstractions
- **Equal plane** — Users and models as equivalent principals

If you agree, read on.

---

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Standards](#code-standards)
- [Testing Guidelines](#testing-guidelines)
- [Contribution Workflow](#contribution-workflow)
- [Architecture Guidelines](#architecture-guidelines)
- [Documentation](#documentation)
- [Community](#community)

---

## Getting Started

### Prerequisites

- Python 3.10+
- Git
- Basic understanding of quantum computing concepts (helpful but not required)
- Familiarity with FastAPI, Textual, or asyncio (depending on contribution area)

### Quick Start

1. **Fork the repository**
   ```bash
   git clone https://github.com/yourusername/VEILos4.git
   cd VEILos4
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run demo to verify setup**
   ```bash
   python demo.py
   ```

   Expected output: `11/11 sections pass` ✅

5. **Launch interfaces**
   ```bash
   # TUI
   python interfaces/tui.py
   
   # Shell
   python interfaces/shell.py
   
   # Web dashboard
   uvicorn interfaces.web:app --reload --port 8001
   ```

---

## Development Setup

### Directory Structure

```
VEILos4/
├── veil_kernel.py           # Main kernel entry point
├── core/
│   ├── quantum/             # Quantum substrate (DO NOT MODIFY)
│   ├── security/            # Security lattice (DO NOT MODIFY)
│   ├── extensibility/       # Plugin system (DO NOT MODIFY)
│   ├── audit/               # Audit chain (DO NOT MODIFY)
│   ├── modification/        # Self-modification engine
│   │   └── scaffold_engine.py
│   └── providers/           # Cognitive providers
│       └── cognitive_stack.py
├── interfaces/              # User interfaces
│   ├── tui.py              # Textual TUI
│   ├── shell.py            # REPL shell
│   └── web.py              # FastAPI dashboard
├── docs/                    # Documentation
│   ├── USER_GUIDE.md
│   ├── ARCHITECTURE_GUIDE.md
│   ├── API_REFERENCE.md
│   └── DEPLOYMENT.md
├── demo.py                  # Integration test script
└── requirements.txt         # Dependencies
```

### What to Modify

**✅ SAFE TO MODIFY:**
- `veil_kernel.py` — Kernel entry point, intent handlers
- `core/providers/cognitive_stack.py` — Multi-model logic
- `core/modification/scaffold_engine.py` — Scaffolding templates
- `interfaces/` — All interface code
- `docs/` — Documentation

**❌ DO NOT MODIFY (unless you know what you're doing):**
- `core/quantum/` — Quantum substrate (stable, tested)
- `core/security/` — Security lattice (audited)
- `core/extensibility/` — Plugin system (complex dependencies)
- `core/audit/` — Audit chain (immutable logs)
- `core/parity/` — User-model equality primitives

### Environment Variables

```bash
# LLM Providers (optional — falls back to mocks if not set)
export OLLAMA_BASE_URL="http://localhost:11434"
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export XAI_API_KEY="xai-..."

# Kernel Configuration (optional)
export VEIL_DEBUG=true
export VEIL_COGNITIVE_LAYERS=5
export VEIL_AUDIT_ENABLED=true
```

---

## Code Standards

### Python Style

- **PEP 8** with 120-character line limit (not 79)
- **Type hints** for all public methods
- **Docstrings** for all public classes/methods (Google style)

Example:
```python
def process_prompt(self, prompt: str, context: Optional[Dict] = None) -> Dict[str, Any]:
    """Process prompt through cognitive layers.
    
    Args:
        prompt: Input prompt string
        context: Optional execution context
        
    Returns:
        Dictionary containing consensus, confidence, and layer responses
        
    Raises:
        ValueError: If prompt is empty or invalid
    """
    if not prompt:
        raise ValueError("Prompt cannot be empty")
    # ...
```

### Naming Conventions

- Classes: `PascalCase`
- Functions/methods: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private methods: `_leading_underscore`
- Quantum state IDs: `snake_case` (no hyphens)
- Intent types: `snake_case` (e.g., `quantum_create`, `memory_store`)

### Import Order

```python
# Standard library
import os
import time
from typing import Dict, List, Optional

# Third-party
from fastapi import FastAPI
from textual.app import App

# Local
from core.quantum import QuantumState
from core.providers.cognitive_stack import CognitiveStack
```

### Error Handling

Always return structured responses, never raw exceptions:

```python
# ✅ GOOD
try:
    result = dangerous_operation()
    return {'status': 'success', 'data': result}
except ValueError as e:
    return {'status': 'error', 'message': str(e), 'error_type': 'ValueError'}

# ❌ BAD
result = dangerous_operation()  # Uncaught exception
```

---

## Testing Guidelines

### Running Tests

**Integration Test (Primary):**
```bash
python demo.py
```

Expected: `11/11 sections pass` ✅

**Interface Tests:**
```bash
# TUI (manual verification)
python interfaces/tui.py
# Type: "Create quantum state named test"
# Verify: Success message appears

# Shell (manual verification)
python interfaces/shell.py
# Type: "status"
# Verify: System status displayed

# Web (automated + manual)
uvicorn interfaces.web:app --port 8001 &
curl -X POST http://localhost:8001/execute \
  -H "Content-Type: application/json" \
  -d '{"command": "What is the system status?"}'
# Verify: 200 OK with status='success'
```

### Test-Driven Development (TDD)

**For new intent types:**

1. **RED** — Add test case to `demo.py`:
   ```python
   print("13. Testing new_intent...")
   result = kernel.execute("trigger new intent")
   assert result['status'] == 'success', f"Expected success, got {result}"
   assert result['intent_type'] == 'new_intent'
   print("    ✅ new_intent handler works")
   ```

2. **GREEN** — Implement handler in `veil_kernel.py`:
   ```python
   def _handle_new_intent(self, params: Dict) -> Dict:
       # Implementation
       return {'status': 'success', 'intent_type': 'new_intent', 'data': {...}}
   ```

3. **REFACTOR** — Clean up, add error handling, update docs

### What to Test

**Critical Paths (Must Test):**
- All 13 intent types execute successfully
- CognitiveStack returns responses with ≥0.7 confidence
- ScaffoldEngine creates artifacts without errors
- All three interfaces launch without crashes

**Nice to Have:**
- Edge cases (empty commands, invalid state IDs)
- Error recovery (failed LLM calls, missing files)
- Performance benchmarks (cognitive latency, scaffold speed)

### Test Data

Use predictable test values:
```python
# ✅ GOOD
state_id = "test_state_123"
prompt = "What are the implications of quantum computing?"

# ❌ BAD (randomness makes debugging hard)
state_id = f"state_{uuid.uuid4()}"
```

---

## Contribution Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

**Branch naming:**
- `feature/` — New functionality
- `fix/` — Bug fixes
- `docs/` — Documentation only
- `refactor/` — Code cleanup (no behavior change)

### 2. Make Changes

Follow code standards above. Commit frequently with clear messages:

```bash
git commit -m "feat: add quantum teleportation intent handler

- Parse 'teleport state X to Y' commands
- Implement _handle_quantum_teleport()
- Add integration test to demo.py
- Update API_REFERENCE.md with new intent type"
```

**Commit message format:**
```
<type>: <subject>

<body>
```

**Types:**
- `feat` — New feature
- `fix` — Bug fix
- `docs` — Documentation
- `refactor` — Code restructuring
- `test` — Add/update tests
- `chore` — Maintenance (deps, config)

### 3. Test Locally

```bash
# Run integration test
python demo.py  # Expect 11/11 or X+1/X+1 if you added tests

# Test interfaces
python interfaces/tui.py    # Manual verification
python interfaces/shell.py  # Manual verification
uvicorn interfaces.web:app --reload --port 8001  # curl test
```

### 4. Update Documentation

If you changed behavior, update docs:
- `docs/USER_GUIDE.md` — If user-facing
- `docs/API_REFERENCE.md` — If API surface changed
- `docs/ARCHITECTURE_GUIDE.md` — If architecture changed

### 5. Submit Pull Request

```bash
git push origin feature/your-feature-name
```

Then open PR on GitHub with:

**Title:** `feat: add quantum teleportation intent` (same as commit)

**Description:**
```markdown
## Summary
Adds quantum teleportation intent for moving quantum states between systems.

## Changes
- New intent type: `quantum_teleport`
- Handler: `_handle_quantum_teleport()`
- Integration test added to demo.py
- API docs updated

## Testing
- [x] Integration test passes (12/12 sections)
- [x] TUI interface tested manually
- [x] Web API tested with curl

## Breaking Changes
None

## Related Issues
Closes #42
```

### 6. Code Review

Maintainers will review. Common feedback:

- Missing type hints → Add them
- No docstrings → Add them
- Tests failing → Fix before merge
- Documentation missing → Update docs

Address feedback, push changes:
```bash
git commit -m "fix: address PR feedback - add type hints to teleport handler"
git push origin feature/your-feature-name
```

### 7. Merge

Once approved, maintainer will merge. Your contribution is now live! 🎉

---

## Architecture Guidelines

### Quantum Substrate

VEILos4's quantum layer is NOT quantum computing (no qubits). It's a **metaphor** for:

- **Superposition** — Multiple potential outcomes exist until observation
- **Entanglement** — States correlated across system boundaries
- **Coherence** — Maintaining valid relationships between entangled states

Example:
```python
# Create superposition: "What model should answer this?"
candidates = ['claude-3', 'gpt-4', 'llama-3']
state = quantum_mgr.superpose("model_selection", *candidates)

# Observe (collapse): "Let's use claude-3 for reasoning"
chosen = state.observe({'specialization': 'reasoning'})  # → 'claude-3'
```

**When to use quantum operations:**
- Model selection (superposition of candidates)
- Intent disambiguation (multiple interpretations)
- Resource allocation (entangle state across subsystems)

**When NOT to use:**
- Simple data storage (use memory instead)
- Deterministic operations (use normal functions)
- External API calls (not quantum-compatible)

### CognitiveStack Design

**Layer Weighting:**
```python
# Higher priority = more influence on consensus
layer1 = ModelLayer('claude-3', 'anthropic', REASONING, priority=2)  # 2x weight
layer2 = ModelLayer('gpt-4', 'openai', ANALYSIS, priority=1)         # 1x weight
```

**Specialization Mapping:**
- `REASONING` → Logic, proofs, formal analysis
- `MATH` → Numerical computation, statistics
- `CREATIVE` → Writing, storytelling, brainstorming
- `ANALYSIS` → Data interpretation, pattern recognition
- `GENERAL` → Default, balanced capability

**Adding New Providers:**

1. Check `concierge_os/integrations/llm_client.py` supports provider
2. Add environment variable check in `cognitive_stack.py`:
   ```python
   def _should_use_real_llm(self) -> bool:
       return (
           os.getenv('OLLAMA_BASE_URL') or
           os.getenv('OPENAI_API_KEY') or
           os.getenv('YOUR_NEW_PROVIDER_KEY')  # Add here
       )
   ```
3. Update `_generate_llm_response()` provider detection:
   ```python
   if os.getenv('YOUR_NEW_PROVIDER_KEY'):
       response = call_llm(
           model_name=layer.model_name,
           prompt=full_prompt,
           provider='your_provider'  # Add to call_llm
       )
   ```

### ScaffoldEngine Patterns

**Template Structure:**
```python
TEMPLATES = {
    'your_template': {
        'description': 'Brief description',
        'category': 'extensibility|interface|cognitive',
        'files': [
            {
                'path': 'plugins/{name}.py',
                'content': '''
# Template with {name} placeholder
class {ClassName}:
    pass
'''
            }
        ]
    }
}
```

**Intent Parsing:**
Scaffold engine extracts component name from intent:
```python
intent = "create quantum observer plugin"
# Extracts: type='plugin', name='quantum_observer'
```

Use clear naming: `"create X Y"` where Y is unique component name.

### Intent Handler Pattern

All handlers follow same structure:

```python
def _handle_your_intent(self, params: Dict) -> Dict:
    """Handle your_intent commands.
    
    Args:
        params: Intent parameters from parser
        
    Returns:
        Execution result dictionary
    """
    try:
        # 1. Extract params
        required_param = params.get('required_param')
        if not required_param:
            raise ValueError("Missing required_param")
        
        # 2. Execute operation
        result = self.subsystem.operation(required_param)
        
        # 3. Return success
        return {
            'status': 'success',
            'intent_type': 'your_intent',
            'message': f'Operation completed: {result}',
            'data': {'key': result}
        }
        
    except Exception as e:
        # 4. Handle errors
        return {
            'status': 'error',
            'intent_type': 'your_intent',
            'message': str(e)
        }
```

**Register in execute():**
```python
intent_type = intent['intent_type']
if intent_type == 'your_intent':
    return self._handle_your_intent(intent['params'])
```

---

## Documentation

### When to Update Docs

| Change Type | Update Required |
|-------------|-----------------|
| New intent type | API_REFERENCE.md, USER_GUIDE.md |
| New interface | API_REFERENCE.md, USER_GUIDE.md |
| Changed API signature | API_REFERENCE.md |
| New architecture component | ARCHITECTURE_GUIDE.md |
| Bug fix (no API change) | No update needed |
| Configuration option | DEPLOYMENT.md, API_REFERENCE.md |

### Documentation Style

- **USER_GUIDE.md** — Tutorials, examples, "how do I..."
- **API_REFERENCE.md** — Complete API surface, all methods/params
- **ARCHITECTURE_GUIDE.md** — Design decisions, subsystem interactions
- **DEPLOYMENT.md** — Production setup, ops concerns

**Voice:**
- Direct, no fluff
- Assume technical audience
- Code examples > prose
- Show actual output (not `[...]`)

**Example (Good):**
```markdown
### Create Quantum State

```python
result = kernel.execute("Create quantum state named my_state")
# {'status': 'success', 'state_id': 'my_state', ...}
```

State ID must be alphanumeric + underscore only.
```

**Example (Bad):**
```markdown
### Create Quantum State

You can create a quantum state by executing a command! The kernel will process it and return a result. Make sure to follow naming conventions for best results.
```

---

## Community

### Communication

- **GitHub Issues** — Bug reports, feature requests
- **Pull Requests** — Code contributions
- **Discussions** — Design debates, philosophy questions

### Code of Conduct

- **Be direct** — Say what you mean, no corporate speak
- **Be respectful** — Attack ideas, not people
- **Be constructive** — "This sucks" → "This could be improved by..."
- **Assume good intent** — Most mistakes are honest mistakes

### Getting Help

**Before asking:**
1. Read `docs/USER_GUIDE.md`
2. Check `docs/API_REFERENCE.md`
3. Run `python demo.py` to verify your setup
4. Search existing GitHub issues

**When asking:**
- Show code (not "I tried X and it didn't work")
- Include error messages (full traceback)
- Describe expected vs actual behavior
- Mention environment (OS, Python version, venv activated?)

Example (Good):
```
I'm getting ModuleNotFoundError when running demo.py.

Environment:
- Ubuntu 22.04
- Python 3.11.5
- Fresh git clone

Error:
```
ModuleNotFoundError: No module named 'textual'
```

What I tried:
- Verified requirements.txt exists
- ran `pip install -r requirements.txt` (no errors)

Expected: demo.py runs and shows 11/11 pass
Actual: Crashes with above error
```

Example (Bad):
```
demo doesn't work help
```

---

## Advanced Topics

### Adding New Subsystems

1. Create module in `core/your_subsystem/`
2. Implement interface compatible with existing subsystems
3. Initialize in `VEILKernel.start()`:
   ```python
   self.your_subsystem = YourSubsystem(config=self.config)
   self.subsystems['your_subsystem'] = self.your_subsystem
   ```
4. Add intent handlers that call `self.your_subsystem.method()`
5. Update `ARCHITECTURE_GUIDE.md`

### Custom Interfaces

VEILos4 supports multiple interfaces (TUI, shell, web). To add your own:

1. Create `interfaces/your_interface.py`
2. Import `VEILKernel`
3. Call `kernel.execute(user_input)` for each command
4. Display `result['message']` to user
5. Handle errors (`result['status'] == 'error'`)

Example:
```python
from veil_kernel import VEILKernel

kernel = VEILKernel()
kernel.start()

while True:
    user_input = your_input_method()
    result = kernel.execute(user_input)
    your_display_method(result['message'])
    if result['status'] == 'error':
        your_error_display(result)
```

### Plugin Development

(ScaffoldEngine templates handle most plugin creation, but for custom plugins:)

1. Create `plugins/your_plugin.py`
2. Implement required interfaces (varies by plugin type)
3. Register in kernel or subsystem
4. Test with integration test

---

## Release Process (Maintainers Only)

### Version Numbering

Semantic versioning: `MAJOR.MINOR.PATCH`

- `MAJOR` — Breaking API changes
- `MINOR` — New features (backward compatible)
- `PATCH` — Bug fixes (backward compatible)

### Release Checklist

- [ ] All tests pass (`python demo.py` → 11/11)
- [ ] All interfaces launch successfully
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped in `__init__.py` or `pyproject.toml`
- [ ] Git tag created: `git tag v1.2.3`
- [ ] Pushed to main: `git push origin main --tags`
- [ ] GitHub release created with notes

---

## Questions?

- **Architecture questions** → Open GitHub Discussion
- **Bug reports** → Open GitHub Issue
- **Code questions** → Read `ARCHITECTURE_GUIDE.md`, then ask in Discussion
- **Feature requests** → Open GitHub Issue with `[Feature Request]` prefix

---

## License

By contributing, you agree to license your contributions under the same license as the project (see LICENSE file).

---

## Thank You

VEILos4 exists because of contributors like you. Every PR, every bug report, every documentation fix makes the project better.

Welcome to the veil-lifting community. 🎭

```
    \   ^__^
     \  (oo)\_______
        (__)\       )\/\
            ||----w |
            ||     ||

    moo. ship it.
```
