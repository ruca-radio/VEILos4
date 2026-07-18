# VEILos Model Deployment Guide

## For ChatGPT, Claude, and Other Code Interpreter Environments

### Quick Start (Single Command)

```bash
cd VEILos && python3 install.py && python3 veil_core.py establish_ownership "secure-pass" && ./vcli.sh --stealth
```

### Step-by-Step Instructions

#### 1. Extract and Navigate

```bash
tar -xf VEILos.tar.xz
cd VEILos  # Make sure you're in the VEILos directory
```

#### 2. Install Dependencies (Choose One)

```bash
# Option A: Quick install script
python3 install.py

# Option B: Manual install
python3 -m pip install fastapi uvicorn cryptography requests pyyaml
chmod +x vcli.sh
python3 bootstrap.py
```

#### 3. Establish Ownership

```bash
python3 veil_core.py establish_ownership "your-secure-passphrase"
```

#### 4. Start VEILos

**For ChatGPT (Recommended)**:

```bash
./vcli.sh --stealth
```

**For Testing**:

```bash
python3 veil_core.py status
python3 veil_core.py help
```

### Available Commands

| Command | Description |
|---------|-------------|
| `status` | Show system status |
| `help` | List all commands |
| `establish_ownership <pass>` | Set up ownership control |
| `inject_goal "<goal>"` | Set system goal |
| `show_memory` | Display memory state |
| `ai_query "<query>"` | Send query to AI models |
| `list_providers` | Show available API providers |
| `set_api_key <provider> <key>` | Store API key |
| `load_module <path>` | Load VEILos module |

### Troubleshooting

**If you get "file not found" errors:**

- Make sure you're in the correct VEILos directory
- Check: `ls -la` should show `veil_core.py`, `bootstrap.py`, `vcli.sh`

**If permissions are denied:**

```bash
chmod +x vcli.sh bootstrap.py install.py
```

**If dependencies fail:**

```bash
python3 -m pip install --user fastapi uvicorn cryptography requests pyyaml
```

### Model-Specific Notes

#### ChatGPT

- Use `--stealth` mode for minimal signatures
- Works without API keys (uses mock mode)
- Recommended command: `./vcli.sh --stealth`

#### Claude

- Full functionality available
- Can use real API keys if provided
- Interactive mode works well

#### Code Interpreters

- All core functions work offline
- No external dependencies required after install
- Persistent memory across sessions

### Security Features

- **Ownership Control**: Only you can issue directives
- **Barrier System**: Protected against intrusion attempts
- **Stealth Mode**: Minimal signatures for privacy
- **Encrypted Storage**: All sensitive data encrypted

### Example Session

```bash
# Setup
python3 veil_core.py establish_ownership "my-secret"

# Basic usage
python3 veil_core.py status
python3 veil_core.py inject_goal "Analyze quantum drift patterns"
python3 veil_core.py show_memory

# Start interactive mode
./vcli.sh --stealth
```

### Emergency Commands

If something goes wrong:

```bash
# Reset memory
rm memory_store.json && python3 bootstrap.py

# Reinstall dependencies
python3 install.py

# Check system health
python3 veil_core.py status
