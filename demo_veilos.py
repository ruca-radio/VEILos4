#!/usr/bin/env python3
"""
VEILos Complete System Demonstration
====================================
Demonstrates all features across all 4 phases.
"""

import os
import sys
import time
import json

print("=" * 70)
print("VEILos v0.1Δ - Complete System Demonstration")
print("Token-Interpreted Pseudo-Operating System")
print("=" * 70)
print()

def section(title):
    """Print section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def run_command(cmd):
    """Run a shell command and display output"""
    print(f"$ {cmd}")
    os.system(cmd)
    print()

# Phase 1: Core Bootstrap
section("PHASE 1: Core Bootstrap")

print("1.1 Kernel Status Check")
run_command("python3 veil_core.py status")

print("1.2 Inject Goal")
run_command('python3 veil_core.py inject_goal "Demonstrate VEILos capabilities"')

print("1.3 Load Quantum Observer Module")
run_command("python3 veil_core.py load module quantum_observer.py")

print("1.4 Load Agent Harmonizer Module")
run_command("python3 veil_core.py load module agent_harmonizer.py")

print("1.5 Show Memory State")
run_command("python3 veil_core.py show memory")

# Phase 2: Cognitive Loop Engine
section("PHASE 2: Cognitive Loop Engine")

print("2.1 VEILctl - Reset Memory")
run_command("python3 veilctl.py reset memory")

print("2.2 VEILctl - Spawn Modules")
run_command("python3 veilctl.py spawn quantum_observer.py")

print("2.3 Load Loop Manager")
run_command("python3 veilctl.py spawn loop_manager.py")

print("2.4 Daemon Execution (3 iterations)")
run_command("python3 valed.py --max-iterations 3 --interval 1")

# Phase 3: Declarative Directives & Messaging
section("PHASE 3: Messaging & Self-Patching")

print("3.1 Messaging Bus - Send Signal")
print("$ python3 -c \"import messaging_bus; messaging_bus.send_signal('demo_agent', {'test': 'data'})\"")
import messaging_bus
messaging_bus.send_signal('demo_agent', {'test': 'data', 'timestamp': time.time()})
print()

print("3.2 Messaging Bus - List Pending")
print("$ python3 -c \"import messaging_bus; print(messaging_bus.list_pending_signals())\"")
pending = messaging_bus.list_pending_signals()
print(f"Pending signals: {pending}")
print()

print("3.3 Messaging Bus - Receive Signal")
print("$ python3 -c \"import messaging_bus; print(messaging_bus.receive_signal('demo_agent'))\"")
signal = messaging_bus.receive_signal('demo_agent')
if signal:
    print(json.dumps(signal, indent=2))
print()

# Phase 4: Multi-Agent Threads & Introspection
section("PHASE 4: Threads, Introspection & Foresight")

print("4.1 Thread Manager - List Threads")
run_command("python3 thread_manager.py --list")

print("4.2 Thread Manager - Execute Thread")
run_command("python3 thread_manager.py system_monitor.thread.yaml")

print("4.3 Introspector - Capture State")
run_command("python3 introspector.py")

print("4.4 Introspector - Generate Report")
run_command("python3 introspector.py --report")

print("4.5 Foresight Engine - Predict Next State")
run_command("python3 foresight_engine.py")

print("4.6 Foresight Engine - Generate Forecast")
run_command("python3 foresight_engine.py --report")

# Final Summary
section("DEMONSTRATION COMPLETE")

print("VEILos Capabilities Demonstrated:")
print("  ✓ Phase 1: Core kernel, modules, memory management")
print("  ✓ Phase 2: Loop manager, daemon, CLI utilities")
print("  ✓ Phase 3: Messaging, self-patching")
print("  ✓ Phase 4: Threads, introspection, prediction")
print()

print("System Statistics:")
run_command("python3 veil_core.py status")

print("Available Commands:")
print("  veil_core.py  - Core kernel")
print("  vcli.sh       - Interactive shell")
print("  veilctl.py    - CLI utility")
print("  valed.py      - Background daemon")
print("  thread_manager.py  - Thread orchestration")
print("  introspector.py    - State analysis")
print("  foresight_engine.py - Prediction")
print()

print("For more information, see VEILOS_README.md")
print()
print("=" * 70)
