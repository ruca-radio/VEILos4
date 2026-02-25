#!/usr/bin/env python3
"""
VEILos4 Terminal User Interface (TUI)

Minimalist terminal interface for VEILos4 using textual framework.
Provides natural language command input and real-time status display.
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Static, Input, RichLog
from textual.binding import Binding
from rich.panel import Panel
from rich.text import Text
from datetime import datetime
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from veil_kernel import VEILKernel
from core.providers.cognitive_stack import (
    CognitiveStack,
    ModelLayer,
    ModelSpecialization,
)


class StatusPanel(Static):
    """Live status display"""

    def __init__(self):
        super().__init__()
        self.kernel_status = "Not started"
        self.layers_count = 0
        self.last_command = "None"

    def update_status(self, kernel_status=None, layers_count=None, last_command=None):
        if kernel_status is not None:
            self.kernel_status = kernel_status
        if layers_count is not None:
            self.layers_count = layers_count
        if last_command is not None:
            self.last_command = last_command
        self.refresh()

    def render(self) -> Panel:
        status_text = Text()
        status_text.append("🔮 Kernel: ", style="bold cyan")
        status_text.append(
            f"{self.kernel_status}\n",
            style="green" if self.kernel_status == "Running" else "yellow",
        )
        status_text.append("🧠 Layers: ", style="bold cyan")
        status_text.append(f"{self.layers_count}\n", style="white")
        status_text.append("📝 Last: ", style="bold cyan")
        status_text.append(f"{self.last_command}", style="dim")

        return Panel(status_text, title="VEILos4 Status", border_style="cyan")


class CommandLog(RichLog):
    """Command history and output log"""

    def __init__(self):
        super().__init__(highlight=True, markup=True, auto_scroll=True)

    def log_command(self, command: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.write(f"[cyan]{timestamp}[/cyan] [bold]>[/bold] {command}")

    def log_result(self, result: dict):
        status = result.get("status", "unknown")
        message = result.get("message", "No message")

        if status == "success":
            self.write(f"  [green]✓[/green] {message}")
        else:
            self.write(f"  [red]✗[/red] {message}")

        # Show additional data if present
        if "data" in result and result["data"]:
            data = result["data"]
            if isinstance(data, dict):
                for key, value in data.items():
                    self.write(f"    {key}: {value}")

        self.write("")  # Blank line


class VEILosTUI(App):
    """VEILos4 Terminal User Interface"""

    CSS = """
    Screen {
        layout: grid;
        grid-size: 2 3;
        grid-rows: auto 1fr auto;
    }
    
    StatusPanel {
        column-span: 2;
        height: 8;
    }
    
    CommandLog {
        column-span: 2;
        border: solid cyan;
    }
    
    Input {
        column-span: 2;
        dock: bottom;
    }
    
    Header {
        background: $primary;
    }
    
    Footer {
        background: $primary;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=True),
        Binding("ctrl+l", "clear_log", "Clear", show=True),
    ]

    TITLE = "VEILos4 - Quantum Cognitive Liberation Architecture"
    SUB_TITLE = "Natural Language Interface"

    def __init__(self):
        super().__init__()
        self.kernel = None
        self.stack = None

    def compose(self) -> ComposeResult:
        """Create child widgets"""
        yield Header()
        yield StatusPanel()
        yield CommandLog()
        yield Input(placeholder="Enter command (natural language)...")
        yield Footer()

    def on_mount(self) -> None:
        """Initialize kernel when app starts"""
        self.log_panel = self.query_one(CommandLog)
        self.status_panel = self.query_one(StatusPanel)
        self.input_field = self.query_one(Input)

        # Initialize kernel
        self.log_panel.write("[yellow]Initializing VEILos4 kernel...[/yellow]")
        try:
            self.kernel = VEILKernel()
            self.kernel.start()

            self.stack = CognitiveStack()
            self.stack.add_layer(
                ModelLayer("claude-3", "anthropic", ModelSpecialization.REASONING)
            )
            self.stack.add_layer(
                ModelLayer("qwen-72b", "ollama", ModelSpecialization.MATH)
            )

            self.status_panel.update_status(kernel_status="Running", layers_count=2)

            self.log_panel.write("[green]✓ Kernel initialized[/green]")
            self.log_panel.write("[green]✓ Cognitive stack ready (2 layers)[/green]")
            self.log_panel.write("")
            self.log_panel.write("[bold cyan]Ready for commands![/bold cyan]")
            self.log_panel.write("[dim]Type 'help' for available commands[/dim]")
            self.log_panel.write("")

        except Exception as e:
            self.log_panel.write(f"[red]✗ Initialization failed: {e}[/red]")
            self.status_panel.update_status(kernel_status="Error")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle command submission"""
        command = event.value.strip()
        if not command:
            return

        # Clear input
        self.input_field.value = ""

        # Log command
        self.log_panel.log_command(command)
        self.status_panel.update_status(last_command=command[:40])

        # Special commands
        if command.lower() in ["quit", "exit"]:
            self.exit()
            return

        if command.lower() == "clear":
            self.log_panel.clear()
            return

        # Execute via kernel
        try:
            result = self.kernel.execute(command, agent_id="tui_user")
            self.log_panel.log_result(result)
        except Exception as e:
            self.log_panel.log_result(
                {"status": "error", "message": f"Execution failed: {str(e)}"}
            )

    def action_clear_log(self) -> None:
        """Clear the command log"""
        self.log_panel.clear()
        self.log_panel.write("[dim]Log cleared[/dim]")
        self.log_panel.write("")


def main():
    """Entry point"""
    app = VEILosTUI()
    app.run()


if __name__ == "__main__":
    main()
