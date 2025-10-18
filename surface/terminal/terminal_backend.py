"""
VEIL4 Terminal Backend

Python backend integration for the VEILos4 Terminal Console.
Provides API endpoints for terminal commands and VEIL4 system interaction.
"""

from typing import Dict, Any, Optional, List
import json
from datetime import datetime

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
        
        return {
            "session_id": session_id,
            "agent_id": agent_id,
            "status": "active",
            "veil4_running": self.veil4.running
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
            else:
                output = f"Unknown command: {cmd}"
            
            return {
                "success": True,
                "output": output,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "output": f"Error executing command: {e}"
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

System Commands:
  status                        - Show system status
  help                          - Show this help message

════════════════════════════════════════════════════════════"""
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a terminal session"""
        return self.terminal_sessions.get(session_id)
    
    def close_session(self, session_id: str) -> bool:
        """Close a terminal session"""
        if session_id in self.terminal_sessions:
            self.terminal_sessions[session_id]["state"] = "closed"
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
