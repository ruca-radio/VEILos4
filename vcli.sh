#!/bin/bash

# VEILos CLI Shell - Now with stealth mode

STEALTH_MODE=false

# Check for stealth flag
if [[ "$1" == "--stealth" ]]; then
    STEALTH_MODE=true
    shift
fi

if [ "$STEALTH_MODE" = true ]; then
    export VEIL_STEALTH=1
else
    unset VEIL_STEALTH
fi

echo "🧠 VEILos CLI v0.1Δ"
if [ "$STEALTH_MODE" = true ]; then
    echo "[Stealth Mode Active]"
else
    echo "[Development Mode]"
fi
echo "Type 'help' for available commands or 'exit' to quit."
echo ""

while true; do
    if [ "$STEALTH_MODE" = true ]; then
        read -p "> " cmd
    else
        read -p "veilos> " cmd
    fi

    if [ "$cmd" = "exit" ]; then
        echo "Goodbye."
        break
    fi

    # Pass stealth flag to core
    if [ "$STEALTH_MODE" = true ]; then
        python3 veil_core.py "$cmd" --stealth
    else
        python3 veil_core.py "$cmd"
    fi
done
