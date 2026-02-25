#!/usr/bin/env python3
"""
VEILos4 REPL Shell Interface
============================

Simple readline-based REPL for natural language command execution.
Routes commands to VEILKernel.execute() and displays formatted results.

Usage:
    python interfaces/shell.py
"""

import sys
import os
import readline
from pathlib import Path

# Ensure imports work from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from veil_kernel import VEILKernel


class VEILShell:
    """REPL shell for VEILos4 kernel."""

    def __init__(self):
        self.kernel = VEILKernel()
        self.running = False
        self.history_file = Path.home() / ".veilos_history"
        self._load_history()

    def _load_history(self):
        """Load command history from file."""
        if self.history_file.exists():
            try:
                with open(self.history_file, "r") as f:
                    for line in f:
                        readline.add_history(line.strip())
            except Exception:
                pass

    def _save_history(self):
        """Save command history to file."""
        try:
            with open(self.history_file, "w") as f:
                for i in range(readline.get_current_history_length()):
                    f.write(readline.get_history_item(i + 1) + "\n")
        except Exception:
            pass

    def _format_result(self, result: dict) -> str:
        """Format kernel result for display."""
        status = result.get("status", "unknown")
        icon = "✓" if status == "success" else "✗"
        lines = [f"\n{icon} Status: {status}"]

        message = result.get("message", "")
        if message:
            lines.append(f"  Message: {message}")

        data = result.get("data", {})
        if data:
            lines.append("  Data:")
            for key, value in data.items():
                val_str = str(value)
                if len(val_str) > 70:
                    val_str = val_str[:67] + "..."
                lines.append(f"    {key}: {val_str}")

        # Include state_id if present (from quantum operations)
        if "state_id" in result:
            lines.append(f"  State ID: {result['state_id']}")

        return "\n".join(lines)

    def _show_banner(self):
        """Display welcome banner."""
        print(
            """
╔═══════════════════════════════════════════════════════════╗
║         VEILos4 REPL Shell                                ║
║         Quantum-Cognitive Operating System                ║
╚═══════════════════════════════════════════════════════════╝

Type 'help' for commands, 'exit' or 'quit' to leave.
"""
        )

    def _show_help(self):
        """Display help information."""
        help_text = """
Available Commands:
  help                    Show this help message
  exit, quit              Exit the shell
  
Quantum Operations:
  create quantum state <id> with options <opt1>, <opt2>, ...
  observe state <id> as <agent>
  
Agent Management:
  register agent <name>
  list agents
  
Security:
  grant capability to <resource>
  
Cognitive Stack:
  show stack info
  think about <topic>
  
Scaffolding:
  list available templates
  
System:
  show system status
  veilos status
  
Examples:
  > create quantum state decision_001 with options alpha, beta, gamma
  > observe state decision_001 as demo_user
  > register agent researcher
  > think about quantum computing implications
"""
        print(help_text)

    def run(self):
        """Run the REPL loop."""
        self._show_banner()

        # Boot kernel
        try:
            boot_result = self.kernel.start()
            print(f"✓ Kernel booted")
            print(f"  Subsystems: {boot_result.get('subsystems', 'N/A')}")
            print(f"  Status: {boot_result.get('status', 'N/A')}\n")
        except Exception as e:
            print(f"✗ Kernel boot failed: {e}")
            return

        self.running = True

        while self.running:
            try:
                prompt = "veilos> "
                user_input = input(prompt).strip()

                if not user_input:
                    continue

                # Handle special commands
                if user_input.lower() in ("exit", "quit"):
                    self._shutdown()
                    break

                if user_input.lower() == "help":
                    self._show_help()
                    continue

                # Execute command via kernel
                try:
                    result = self.kernel.execute(user_input)
                    print(self._format_result(result))
                except Exception as e:
                    print(f"\n✗ Execution error: {e}")

            except KeyboardInterrupt:
                print("\n\n(Interrupted. Type 'exit' to quit.)")
            except EOFError:
                print()
                self._shutdown()
                break

    def _shutdown(self):
        """Shutdown kernel and save history."""
        print("\nShutting down...")
        try:
            result = self.kernel.shutdown()
            print(f"✓ {result.get('message', 'Shutdown complete')}")
        except Exception as e:
            print(f"✗ Shutdown error: {e}")
        finally:
            self._save_history()
            self.running = False


def main():
    """Entry point."""
    shell = VEILShell()
    shell.run()


if __name__ == "__main__":
    main()
