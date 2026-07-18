# VEILos Quick Start Guide 🚀

## Instant Setup (3 steps)

### 1. Bootstrap the System
```bash
python bootstrap.py
```
This will:
- Check Python version (3.11+ required)
- Install dependencies
- Initialize all directories
- Set up security keys
- Run health checks

### 2. Start VEILos
```bash
# Option A: Interactive CLI
./vcli.sh

# Option B: Web Interface
uvicorn veil_webchat:app --reload
# Then open http://localhost:8000

# Option C: Background Daemon
python valed.py
```

### 3. First Commands
```
# In the CLI:
help                           # Show available commands
status                         # Check system status
inject_goal "Test VEILos"      # Set a goal
show memory                    # View system memory
load module quantum_observer.py # Load a module
```

## Working with AI Models

### Mock Mode (No API Keys Needed)
```
# VEILos includes mock responses for testing:
ai_query Claude, explain quantum computing
```

### Real API Mode
```
# Set your API key:
set_api_key anthropic YOUR_API_KEY

# Query the real API:
ai_query Claude, what is VEILos?
```

## Troubleshooting

### Dependencies Issues
```bash
# Manual install if bootstrap fails:
pip install -r requirements.txt
```

### API Connection Issues
- VEILos automatically falls back to mock mode
- Check `list_providers` to see available options
- Ensure API keys are set with `set_api_key`

### Session Recovery
```bash
# Export current session:
veilctl export-session my-session.veilsession

# Resume later:
veilctl load-session my-session.veilsession
```

## Next Steps
- Read the full README.md for detailed documentation
- Explore modules in the `modules/` directory
- Check `directives/` for advanced scripting
- Join the VEILos community (coming soon)
