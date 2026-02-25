"""
VEIL4 Terminal Backend

Python backend integration for the VEILos4 Terminal Console.
Provides API endpoints for terminal commands and VEIL4 system interaction.
Supports dual mode: VEILos commands and Linux shell emulation.
"""

from typing import Dict, Any, Optional, List
import json
import subprocess
import os
import shlex
from datetime import datetime
from pathlib import Path

from core.veil4_system import VEIL4
from core.parity.unified_interface import AgentType


class TerminalBackend:
    """
    Backend service for VEILos4 Terminal Console.
    
    Provides command execution, state management, and VEIL4 integration.
    """
    
    def __init__(self, veil4: Optional[VEIL4] = None):
        """
        Initialize terminal backend.
        
        Args:
            veil4: Optional VEIL4 system instance (creates new if None)
        """
        self.veil4 = veil4 or VEIL4()
        self.terminal_sessions: Dict[str, Dict[str, Any]] = {}
        self.command_history: List[Dict[str, Any]] = []
        
        # Linux shell state for each session
        self.shell_states: Dict[str, Dict[str, Any]] = {}
        
    def start(self):
        """Start the terminal backend and VEIL4 system"""
        if not self.veil4.running:
            self.veil4.start()
    
    def create_session(
        self, 
        session_id: str, 
        boot_settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new terminal session.
        
        Args:
            session_id: Unique session identifier
            boot_settings: Boot configuration from frontend
            
        Returns:
            Session info
        """
        self.terminal_sessions[session_id] = {
            "id": session_id,
            "created_at": datetime.now().isoformat(),
            "boot_settings": boot_settings,
            "agent_id": None,
            "state": "active"
        }
        
        # Register terminal agent if user specified
        if boot_settings.get("userMode") == "sudo":
            agent_id = f"terminal_session_{session_id}_sudo"
            capabilities = ["read", "write", "execute", "admin"]
        else:
            agent_id = f"terminal_session_{session_id}_user"
            capabilities = ["read", "execute"]
        
        self.veil4.register_agent(
            agent_id=agent_id,
            agent_type=AgentType.HUMAN,
            capabilities=capabilities,
            metadata={"session_id": session_id}
        )
        
        self.terminal_sessions[session_id]["agent_id"] = agent_id
        
        # Initialize shell state for this session
        self.shell_states[session_id] = {
            "cwd": str(Path.home()),  # Start in home directory
            "env": dict(os.environ),  # Copy current environment
            "shell": "bash"  # Default shell
        }
        
        return {
            "session_id": session_id,
            "agent_id": agent_id,
            "status": "active",
            "veil4_running": self.veil4.running,
            "shell_enabled": True,
            "cwd": self.shell_states[session_id]["cwd"]
        }
    
    def execute_command(
        self, 
        session_id: str, 
        command: str
    ) -> Dict[str, Any]:
        """
        Execute a terminal command.
        
        Args:
            session_id: Session identifier
            command: Command string to execute
            
        Returns:
            Command execution result
        """
        if session_id not in self.terminal_sessions:
            return {
                "success": False,
                "error": "Invalid session ID",
                "output": ""
            }
        
        session = self.terminal_sessions[session_id]
        agent_id = session["agent_id"]
        
        # Log command
        command_record = {
            "session_id": session_id,
            "agent_id": agent_id,
            "command": command,
            "timestamp": datetime.now().isoformat()
        }
        self.command_history.append(command_record)
        
        # Parse and execute command
        parts = command.strip().split()
        if not parts:
            return {"success": True, "output": ""}
        
        cmd = parts[0].lower()
        args = parts[1:]
        
        try:
            # Check if it's a VEILos4 command or Linux command
            if cmd == "quantum":
                output = self._handle_quantum_command(agent_id, args)
            elif cmd == "capability":
                output = self._handle_capability_command(agent_id, args)
            elif cmd == "agent":
                output = self._handle_agent_command(agent_id, args)
            elif cmd == "plugin":
                output = self._handle_plugin_command(agent_id, args)
            elif cmd == "status":
                output = self._get_system_status()
            elif cmd == "help":
                output = self._get_help_text()
            elif cmd == "linux":
                # Explicit linux command prefix
                linux_cmd = " ".join(args)
                output = self._execute_linux_command(session_id, agent_id, linux_cmd)
            elif cmd == "shell":
                # Shell mode toggle or explicit shell command
                output = self._handle_shell_command(session_id, args)
            else:
                # Try to execute as Linux command if it looks like one
                output = self._try_linux_or_veil_command(session_id, agent_id, command)
            
            return {
                "success": True,
                "output": output,
                "timestamp": datetime.now().isoformat(),
                "cwd": self.shell_states.get(session_id, {}).get("cwd", "")
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "output": f"Error executing command: {e}",
                "cwd": self.shell_states.get(session_id, {}).get("cwd", "")
            }
    
    def _handle_quantum_command(self, agent_id: str, args: List[str]) -> str:
        """Handle quantum-related commands"""
        if not args:
            return "Usage: quantum <create|observe|list> [args]"
        
        subcommand = args[0].lower()
        
        if subcommand == "create":
            if len(args) < 2:
                return "Usage: quantum create <state_id>"
            
            state_id = args[1]
            # Create example superposition
            self.veil4.create_quantum_state(
                state_id=state_id,
                states=[
                    {"choice": "A", "probability": 0.5},
                    {"choice": "B", "probability": 0.5}
                ]
            )
            return f"✓ Quantum state '{state_id}' created with 2 superposed states"
        
        elif subcommand == "observe":
            if len(args) < 2:
                return "Usage: quantum observe <state_id>"
            
            state_id = args[1]
            try:
                result = self.veil4.observe_quantum_state(state_id, agent_id)
                return f"✓ Quantum state collapsed to: {json.dumps(result, indent=2)}"
            except KeyError:
                return f"✗ Quantum state '{state_id}' not found"
        
        elif subcommand == "list":
            states = list(self.veil4.quantum.superpositions.keys())
            if not states:
                return "No active quantum states"
            return f"Active quantum states:\n" + "\n".join(f"  • {s}" for s in states)
        
        else:
            return f"Unknown quantum subcommand: {subcommand}"
    
    def _handle_capability_command(self, agent_id: str, args: List[str]) -> str:
        """Handle capability-related commands"""
        if not args:
            return "Usage: capability <grant|verify|revoke> [args]"
        
        subcommand = args[0].lower()
        
        if subcommand == "grant":
            if len(args) < 4:
                return "Usage: capability grant <agent_id> <resource> <permissions>"
            
            target_agent = args[1]
            resource = args[2]
            permissions = args[3].split(",")
            
            token = self.veil4.grant_capability(
                resource=resource,
                permissions=permissions,
                agent_id=target_agent,
                duration_seconds=3600
            )
            return f"✓ Capability granted to {target_agent}\nToken: {token}"
        
        elif subcommand == "verify":
            if len(args) < 4:
                return "Usage: capability verify <agent_id> <resource> <permission> <token>"
            
            target_agent = args[1]
            resource = args[2]
            permission = args[3]
            token = args[4] if len(args) > 4 else ""
            
            verified = self.veil4.verify_access(
                agent_id=target_agent,
                resource=resource,
                permission=permission,
                capability_token=token
            )
            
            return f"✓ Access {'granted' if verified else 'denied'}"
        
        else:
            return f"Unknown capability subcommand: {subcommand}"
    
    def _handle_agent_command(self, agent_id: str, args: List[str]) -> str:
        """Handle agent-related commands"""
        if not args:
            return "Usage: agent <register|list|info> [args]"
        
        subcommand = args[0].lower()
        
        if subcommand == "register":
            if len(args) < 3:
                return "Usage: agent register <agent_id> <type>"
            
            new_agent_id = args[1]
            agent_type_str = args[2].upper()
            
            try:
                agent_type = AgentType[agent_type_str]
                self.veil4.register_agent(
                    agent_id=new_agent_id,
                    agent_type=agent_type,
                    capabilities=["read", "execute"]
                )
                return f"✓ Agent '{new_agent_id}' registered as {agent_type_str}"
            except KeyError:
                return f"✗ Invalid agent type: {agent_type_str}. Use HUMAN or MODEL."
        
        elif subcommand == "list":
            agents = list(self.veil4.parity.agents.keys())
            if not agents:
                return "No registered agents"
            return f"Registered agents:\n" + "\n".join(f"  • {a}" for a in agents)
        
        elif subcommand == "info":
            if len(args) < 2:
                return "Usage: agent info <agent_id>"
            
            target_agent = args[1]
            if target_agent in self.veil4.parity.agents:
                agent = self.veil4.parity.agents[target_agent]
                return f"Agent: {agent.agent_id}\nType: {agent.agent_type.value}\nCapabilities: {agent.capabilities}"
            else:
                return f"✗ Agent '{target_agent}' not found"
        
        else:
            return f"Unknown agent subcommand: {subcommand}"
    
    def _handle_plugin_command(self, agent_id: str, args: List[str]) -> str:
        """Handle plugin-related commands"""
        if not args:
            return "Usage: plugin <list|load|unload> [args]"
        
        subcommand = args[0].lower()
        
        if subcommand == "list":
            plugins = list(self.veil4.plugins.plugins.keys())
            if not plugins:
                return "No plugins loaded"
            return f"Loaded plugins:\n" + "\n".join(f"  • {p}" for p in plugins)
        
        elif subcommand == "load":
            if len(args) < 2:
                return "Usage: plugin load <plugin_name>"
            
            plugin_name = args[1]
            # In a real implementation, this would load the actual plugin
            return f"✓ Plugin '{plugin_name}' loaded (simulated)"
        
        elif subcommand == "unload":
            if len(args) < 2:
                return "Usage: plugin unload <plugin_name>"
            
            plugin_name = args[1]
            try:
                self.veil4.plugins.unload_plugin(plugin_name)
                return f"✓ Plugin '{plugin_name}' unloaded"
            except Exception as e:
                return f"✗ Error unloading plugin: {e}"
        
        else:
            return f"Unknown plugin subcommand: {subcommand}"
    
    def _execute_linux_command(
        self, 
        session_id: str, 
        agent_id: str, 
        command: str
    ) -> str:
        """
        Execute a Linux shell command.
        
        Args:
            session_id: Session identifier
            agent_id: Agent executing the command
            command: Linux command to execute
            
        Returns:
            Command output or error message
        """
        # Security check - verify agent has execute capability
        agent = self.veil4.parity.agents.get(agent_id)
        if not agent or "execute" not in agent.capabilities:
            return "✗ Permission denied: 'execute' capability required for shell commands"
        
        # Get shell state
        shell_state = self.shell_states.get(session_id)
        if not shell_state:
            return "✗ Session shell state not initialized"
        
        # Handle built-in commands that modify state
        if command.startswith("cd "):
            return self._handle_cd_command(session_id, command)
        elif command == "pwd":
            return shell_state["cwd"]
        elif command.startswith("export "):
            return self._handle_export_command(session_id, command)
        
        # Security: block dangerous commands for non-sudo users
        if "admin" not in agent.capabilities:
            dangerous_cmds = ["rm -rf /", "mkfs", "dd if=", ":(){ :|:& };:", "chmod -R 777 /"]
            for danger in dangerous_cmds:
                if danger in command:
                    return f"✗ Security: Command blocked (requires sudo/admin capability)"
        
        try:
            # Execute command in the session's working directory
            result = subprocess.run(
                command,
                shell=True,
                cwd=shell_state["cwd"],
                env=shell_state["env"],
                capture_output=True,
                text=True,
                timeout=30,  # 30 second timeout
                executable="/bin/bash"
            )
            
            # Combine stdout and stderr
            output = ""
            if result.stdout:
                output += result.stdout
            if result.stderr:
                if output:
                    output += "\n"
                output += f"stderr: {result.stderr}"
            
            if result.returncode != 0 and not output:
                output = f"Command exited with code {result.returncode}"
            
            return output if output else "Command completed successfully"
            
        except subprocess.TimeoutExpired:
            return "✗ Command timed out (30s limit)"
        except Exception as e:
            return f"✗ Error executing command: {e}"
    
    def _handle_cd_command(self, session_id: str, command: str) -> str:
        """Handle cd (change directory) command"""
        shell_state = self.shell_states[session_id]
        parts = command.split(maxsplit=1)
        
        if len(parts) == 1:
            # cd with no args goes to home
            target = str(Path.home())
        else:
            target = parts[1].strip()
        
        # Resolve path relative to current directory
        if not target.startswith("/"):
            target = os.path.join(shell_state["cwd"], target)
        
        # Normalize path
        target = os.path.normpath(target)
        
        # Check if directory exists
        if os.path.isdir(target):
            shell_state["cwd"] = target
            return f"Changed directory to: {target}"
        else:
            return f"✗ cd: {target}: No such directory"
    
    def _handle_export_command(self, session_id: str, command: str) -> str:
        """Handle export (environment variable) command"""
        shell_state = self.shell_states[session_id]
        parts = command.split(maxsplit=1)
        
        if len(parts) < 2:
            return "✗ Usage: export VAR=value"
        
        assignment = parts[1]
        if "=" in assignment:
            var, value = assignment.split("=", 1)
            shell_state["env"][var] = value
            return f"✓ Exported: {var}={value}"
        else:
            return "✗ Invalid export syntax. Use: export VAR=value"
    
    def _handle_shell_command(self, session_id: str, args: List[str]) -> str:
        """Handle shell-related commands"""
        if not args:
            shell_state = self.shell_states.get(session_id, {})
            return f"""
Shell Status:
  Shell:        {shell_state.get('shell', 'bash')}
  Working Dir:  {shell_state.get('cwd', 'unknown')}
  
Usage:
  shell info    - Show shell information
  shell env     - Show environment variables
"""
        
        subcommand = args[0].lower()
        shell_state = self.shell_states.get(session_id, {})
        
        if subcommand == "info":
            return f"""
Shell Information:
  Shell:        {shell_state.get('shell', 'bash')}
  Working Dir:  {shell_state.get('cwd', 'unknown')}
  Env Vars:     {len(shell_state.get('env', {}))} defined
"""
        elif subcommand == "env":
            env = shell_state.get("env", {})
            env_lines = [f"  {k}={v}" for k, v in sorted(env.items())]
            return "Environment Variables:\n" + "\n".join(env_lines[:50])  # Limit to 50 vars
        else:
            return f"✗ Unknown shell subcommand: {subcommand}"
    
    def _try_linux_or_veil_command(
        self, 
        session_id: str, 
        agent_id: str, 
        command: str
    ) -> str:
        """
        Try to determine if command is Linux or VEILos4, and execute appropriately.
        
        Common Linux commands will be executed as shell commands.
        Unknown commands will show an error.
        """
        cmd = command.strip().split()[0].lower()
        
        # List of common Linux commands to auto-detect
        common_linux_commands = {
            "ls", "cat", "echo", "grep", "find", "ps", "top", "df", "du",
            "mkdir", "touch", "rm", "cp", "mv", "chmod", "chown", 
            "pwd", "cd", "export", "env", "which", "man", "tail", "head",
            "wc", "sort", "uniq", "diff", "wget", "curl", "ping", "ssh",
            "tar", "gzip", "unzip", "git", "python", "node", "npm", "pip"
        }
        
        if cmd in common_linux_commands:
            # Execute as Linux command
            return self._execute_linux_command(session_id, agent_id, command)
        else:
            # Unknown command
            return f"Unknown command: {cmd}\nTry 'help' for VEILos4 commands or 'linux <cmd>' for shell commands."
    
    def _get_system_status(self) -> str:
        """Get comprehensive system status"""
        status = self.veil4.get_system_status()
        
        return f"""
VEILos4 System Status:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
System:
  Running:                {status['running']}
  Registered Agents:      {status['num_agents']}
  Loaded Plugins:         {status['num_plugins']}

Quantum Substrate:
  Active Superpositions:  {status['num_superpositions']}
  Coherence States:       {status['coherence_states']}

Audit & Transparency:
  State Transitions:      {status['num_transitions']}

Terminal:
  Active Sessions:        {len(self.terminal_sessions)}
  Command History:        {len(self.command_history)}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
    
    def _get_help_text(self) -> str:
        """Get help text for available commands"""
        return """
VEILos4 Terminal Commands:
════════════════════════════════════════════════════════════

Quantum Commands:
  quantum create <id>           - Create a quantum superposition
  quantum observe <id>          - Observe and collapse a state
  quantum list                  - List active quantum states

Capability Commands:
  capability grant <agent> <resource> <perms>
                                - Grant capability to an agent
  capability verify <agent> <resource> <perm> <token>
                                - Verify a capability token

Agent Commands:
  agent register <id> <type>    - Register new agent (HUMAN/MODEL)
  agent list                    - List all registered agents
  agent info <id>               - Show agent information

Plugin Commands:
  plugin list                   - List loaded plugins
  plugin load <name>            - Load a plugin
  plugin unload <name>          - Unload a plugin

Shell Commands:
  linux <command>               - Execute Linux shell command
  shell info                    - Show shell information
  shell env                     - Show environment variables
  cd <directory>                - Change directory
  pwd                           - Print working directory
  export VAR=value              - Set environment variable

Common Linux Commands (auto-detected):
  ls, cat, grep, find, ps, df, mkdir, touch, rm, cp, mv,
  git, python, node, npm, pip, and many more...

System Commands:
  status                        - Show system status
  help                          - Show this help message

════════════════════════════════════════════════════════════
Note: Common Linux commands are auto-detected and executed.
      For explicit shell execution, use: linux <command>
════════════════════════════════════════════════════════════"""
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a terminal session"""
        return self.terminal_sessions.get(session_id)
    
    def close_session(self, session_id: str) -> bool:
        """Close a terminal session"""
        if session_id in self.terminal_sessions:
            self.terminal_sessions[session_id]["state"] = "closed"
            # Cleanup shell state
            if session_id in self.shell_states:
                del self.shell_states[session_id]
            return True
        return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get backend status for health checks"""
        return {
            "running": self.veil4.running,
            "veil4_status": self.veil4.get_system_status(),
            "active_sessions": len([
                s for s in self.terminal_sessions.values() 
                if s["state"] == "active"
            ]),
            "total_sessions": len(self.terminal_sessions),
            "command_history_size": len(self.command_history)
        }
