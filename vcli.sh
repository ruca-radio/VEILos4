#!/bin/bash
# VEILos CLI - Simple bash wrapper for veil_core.py
# Provides REPL-style interface with pipe support

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VEIL_CORE="$SCRIPT_DIR/veil_core.py"

# Check if veil_core.py exists
if [ ! -f "$VEIL_CORE" ]; then
    echo "Error: veil_core.py not found at $VEIL_CORE"
    exit 1
fi

# Make veil_core.py executable if it isn't
if [ ! -x "$VEIL_CORE" ]; then
    chmod +x "$VEIL_CORE"
fi

# If arguments provided, execute command
if [ $# -gt 0 ]; then
    python3 "$VEIL_CORE" "$@"
else
    # Check if input is from pipe
    if [ -p /dev/stdin ]; then
        # Read from pipe
        while IFS= read -r line; do
            python3 "$VEIL_CORE" "$line"
        done
    else
        # Run interactive REPL
        python3 "$VEIL_CORE"
    fi
fi
