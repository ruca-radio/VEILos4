#!/usr/bin/env python3
"""
VEILos Core Kernel
==================
Token-interpreted, directive-driven pseudo-OS kernel that runs inside LLM reasoning layer.

Features:
- Command interpreter (shell-like)
- Synthetic memory persistence (JSON-based)
- Dynamic module loading
- Manifest-based policy enforcement
- Minimal interface: inject_goal, show memory, status, help
"""

import json
import os
import sys
import yaml
import importlib.util
from typing import Dict, Any, List, Optional
from pathlib import Path


class VEILosKernel:
    """
    VEILos Kernel - Core command interpreter and memory manager.
    """
    
    def __init__(self, manifest_path: str = "veil_manifest.yaml", 
                 memory_path: str = "memory_store.json"):
        """
        Initialize VEILos kernel.
        
        Args:
            manifest_path: Path to manifest file
            memory_path: Path to memory store
        """
        self.manifest_path = manifest_path
        self.memory_path = memory_path
        self.manifest = self._load_manifest()
        self.memory = self._load_memory()
        self.loaded_modules = {}
        self.command_history = []
        
        # Ensure required directories exist
        self._ensure_directories()
        
    def _ensure_directories(self):
        """Ensure required directories exist"""
        for directory in ["logs", "tmp", "modules", "veilpkg", "directives"]:
            Path(directory).mkdir(exist_ok=True)
    
    def _load_manifest(self) -> Dict[str, Any]:
        """Load system manifest"""
        try:
            with open(self.manifest_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"[!] Manifest not found at {self.manifest_path}, using defaults")
            return self._default_manifest()
    
    def _default_manifest(self) -> Dict[str, Any]:
        """Return default manifest"""
        return {
            "system": {
                "name": "VEILos",
                "version": "0.1Δ",
                "recursion_depth": 3,
                "entropy_tolerance": 0.05,
                "allow_self_extension": True
            },
            "user": {
                "role": "architect",
                "permissions": [
                    "inject_goal",
                    "load_module",
                    "spawn_agent",
                    "edit_memory"
                ]
            }
        }
    
    def _load_memory(self) -> Dict[str, Any]:
        """Load memory from JSON store"""
        try:
            with open(self.memory_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"[!] Memory not found at {self.memory_path}, initializing")
            return {"goal": "Awaiting injection", "quantum": {}, "action": None}
    
    def _save_memory(self):
        """Save memory to JSON store"""
        with open(self.memory_path, 'w') as f:
            json.dump(self.memory, f, indent=2)
    
    def inject_goal(self, goal: str) -> Dict[str, Any]:
        """
        Inject a goal into system memory.
        
        Args:
            goal: Goal description
            
        Returns:
            Status response
        """
        self.memory["goal"] = goal
        self._save_memory()
        
        result = {"status": "success", "goal": goal, "message": "Goal injected"}
        self._log_operation("inject_goal", result)
        return result
    
    def show_memory(self) -> Dict[str, Any]:
        """
        Display current memory state.
        
        Returns:
            Current memory contents
        """
        return self.memory
    
    def load_module(self, module_name: str) -> Dict[str, Any]:
        """
        Dynamically load and execute a module.
        
        Args:
            module_name: Name of module to load (e.g., "quantum_observer.py")
            
        Returns:
            Module execution result
        """
        module_path = os.path.join("modules", module_name)
        
        if not os.path.exists(module_path):
            return {
                "status": "error",
                "message": f"Module not found: {module_path}"
            }
        
        try:
            # Load module dynamically
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Execute module's run() function if it exists
            if hasattr(module, 'run'):
                result = module.run()
                self.loaded_modules[module_name] = module
                
                result_dict = {
                    "status": "success",
                    "module": module_name,
                    "result": result
                }
            else:
                result_dict = {
                    "status": "loaded",
                    "module": module_name,
                    "message": "Module loaded (no run() function)"
                }
            
            self._log_operation("load_module", result_dict)
            return result_dict
            
        except Exception as e:
            error_result = {
                "status": "error",
                "module": module_name,
                "error": str(e)
            }
            self._log_operation("load_module", error_result)
            return error_result
    
    def status(self) -> Dict[str, Any]:
        """
        Get system status.
        
        Returns:
            Current system status
        """
        return {
            "system": self.manifest.get("system", {}),
            "loaded_modules": list(self.loaded_modules.keys()),
            "memory_state": {
                "goal": self.memory.get("goal"),
                "action": self.memory.get("action"),
                "quantum_keys": list(self.memory.get("quantum", {}).keys())
            },
            "command_history_count": len(self.command_history)
        }
    
    def help(self) -> str:
        """
        Display help information.
        
        Returns:
            Help text
        """
        help_text = """
VEILos Kernel v0.1Δ - Command Reference
========================================

Available Commands:
-------------------
  inject_goal <goal>        Inject a goal into system memory
  show memory               Display current memory state
  load module <module.py>   Load and execute a module
  status                    Show system status
  help                      Display this help message
  exit                      Exit VEILos

Module Loading:
---------------
  Modules are loaded from the 'modules/' directory
  Each module should implement a run() function
  Results are automatically written to memory

Memory Operations:
------------------
  Memory is persisted in JSON format
  Keys: goal, quantum, action
  Modules can read and write memory directly

Examples:
---------
  inject_goal "Harmonize RSI drift"
  load module quantum_observer.py
  show memory
  status
"""
        return help_text
    
    def _log_operation(self, operation: str, result: Dict[str, Any]):
        """Log operation to kernel log"""
        log_entry = {
            "operation": operation,
            "result": result,
            "memory_snapshot": self.memory.copy()
        }
        self.command_history.append(log_entry)
        
        # Write to log file
        log_path = "logs/kernel_boot.log"
        with open(log_path, 'a') as f:
            f.write(json.dumps(log_entry) + "\n")
    
    def execute_command(self, command: str) -> Any:
        """
        Execute a command string.
        
        Args:
            command: Command to execute
            
        Returns:
            Command result
        """
        parts = command.strip().split()
        
        if not parts:
            return None
        
        cmd = parts[0]
        args = parts[1:]
        
        if cmd == "inject_goal":
            if len(args) < 1:
                return {"status": "error", "message": "Usage: inject_goal <goal>"}
            goal = " ".join(args)
            return self.inject_goal(goal)
        
        elif cmd == "show" and len(args) > 0 and args[0] == "memory":
            return self.show_memory()
        
        elif cmd == "load" and len(args) > 1 and args[0] == "module":
            return self.load_module(args[1])
        
        elif cmd == "status":
            return self.status()
        
        elif cmd == "help":
            return self.help()
        
        else:
            return {
                "status": "error",
                "message": f"Unknown command: {cmd}. Type 'help' for available commands."
            }
    
    def repl(self):
        """
        Run interactive REPL (Read-Eval-Print Loop).
        """
        print("=" * 60)
        print("VEILos v0.1Δ - Token-Interpreted Pseudo-OS")
        print("Type 'help' for commands, 'exit' to quit")
        print("=" * 60)
        print()
        
        while True:
            try:
                command = input("veilos> ").strip()
                
                if command.lower() in ["exit", "quit"]:
                    print("Shutting down VEILos...")
                    break
                
                if not command:
                    continue
                
                result = self.execute_command(command)
                
                if result is not None:
                    if isinstance(result, str):
                        print(result)
                    else:
                        print(json.dumps(result, indent=2))
                
            except KeyboardInterrupt:
                print("\nUse 'exit' to quit")
            except Exception as e:
                print(f"Error: {e}")


def main():
    """Main entry point"""
    kernel = VEILosKernel()
    
    # If arguments provided, execute them
    if len(sys.argv) > 1:
        command = " ".join(sys.argv[1:])
        result = kernel.execute_command(command)
        if isinstance(result, str):
            print(result)
        else:
            print(json.dumps(result, indent=2))
    else:
        # Run interactive REPL
        kernel.repl()


if __name__ == "__main__":
    main()
