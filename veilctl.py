#!/usr/bin/env python3
"""
VEILctl - External CLI Utility
===============================
Spawn modules, trigger valescripts, inspect memory, patch operations.
"""

import subprocess
import sys
import json
import os


def run_command(cmd):
    """
    Execute a veil_core.py command.
    
    Args:
        cmd: Command string to execute
    """
    if cmd.startswith("spawn"):
        # spawn module <module.py>
        parts = cmd.split()
        if len(parts) >= 2:
            module = parts[1]
            subprocess.run(["python3", "veil_core.py", "load", "module", module])
        else:
            print("Usage: spawn <module.py>")
    
    elif cmd == "reset memory":
        # Clear memory to default state
        default_memory = {
            "goal": "Awaiting injection",
            "quantum": {},
            "action": None
        }
        with open("memory_store.json", "w") as f:
            json.dump(default_memory, f, indent=2)
        print("[+] Memory reset to default state.")
    
    elif cmd.startswith("inject "):
        # inject <goal>
        _, goal = cmd.split(" ", 1)
        subprocess.run(["python3", "veil_core.py", "inject_goal", goal])
    
    elif cmd.startswith("exec "):
        # exec <valescript>
        _, valescript = cmd.split(" ", 1)
        print(f"[*] Executing valescript: {valescript}")
        # TODO: Implement valescript execution in phase 3
        print("[!] Valescript execution not yet implemented")
    
    elif cmd == "inspect":
        # Show detailed memory inspection
        subprocess.run(["python3", "veil_core.py", "show", "memory"])
    
    elif cmd == "modules":
        # List loaded modules
        subprocess.run(["python3", "veil_core.py", "status"])
    
    else:
        # Pass through to veil_core.py
        cmd_parts = cmd.split()
        subprocess.run(["python3", "veil_core.py"] + cmd_parts)


def show_help():
    """Display veilctl help"""
    help_text = """
VEILctl - VEILos Command Line Utility
======================================

Commands:
---------
  spawn <module.py>      Spawn (load) a module
  reset memory           Reset memory to default state
  inject <goal>          Inject goal into memory
  exec <valescript>      Execute a valescript file (Phase 3)
  inspect                Detailed memory inspection
  modules                List loaded modules and status
  <any veil_core cmd>    Pass through to veil_core.py

Examples:
---------
  veilctl spawn quantum_observer.py
  veilctl reset memory
  veilctl inject "Stabilize quantum drift"
  veilctl inspect
  veilctl status
"""
    print(help_text)


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        show_help()
        return
    
    if sys.argv[1] in ["-h", "--help", "help"]:
        show_help()
        return
    
    # Join all arguments into command
    command = " ".join(sys.argv[1:])
    run_command(command)


if __name__ == "__main__":
    main()
