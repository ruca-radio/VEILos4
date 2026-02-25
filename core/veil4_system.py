"""
VEIL4 Core System

Main integration point for all VEIL4 components.
Coordinates the quantum substrate, security, extensibility, parity, and audit layers.
"""

from typing import Dict, List, Any, Optional
from datetime import timedelta

from core.quantum.superposition import SuperpositionManager
from core.quantum.coherence import CoherenceEngine
from core.security.capabilities import CapabilityManager
from core.extensibility.plugin_manager import PluginManager, PluginType
from core.parity.unified_interface import ParityInterface, UnifiedToolInterface, AgentType
from core.audit.immutable_log import ImmutableLog, ProvenanceTracker


class VEIL4:
    """
    Main VEIL4 Operating System class.
    
    Integrates all layers:
    - Quantum Substrate
    - Capability Security
    - Extensibility Framework
    - Cognitive Parity
    - Audit & Transparency
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize VEIL4 system.
        
        Args:
            config: System configuration
        """
        self.config = config or {}
        
        # Initialize core components
        self.quantum = SuperpositionManager()
        self.coherence = CoherenceEngine(
            default_coherence_time=self.config.get("coherence_time", 60.0)
        )
        self.security = CapabilityManager()
        self.plugins = PluginManager()
        self.parity = ParityInterface()
        self.tools = UnifiedToolInterface()
        self.audit = ImmutableLog()
        self.provenance = ProvenanceTracker()
        
        # System state
        self.running = False
        
    def start(self):
        """Start the VEIL4 system"""
        if self.running:
            return
        
        # Initialize default capabilities
        self._setup_default_capabilities()
        
        # Initialize default tools
        self._setup_default_tools()
        
        self.running = True
        
        # Log system start
        self.audit.log_transition(
            agent_id="system",
            operation="system_start",
            from_state=None,
            to_state={"status": "running"},
            metadata={"config": self.config}
        )
    
    def shutdown(self):
        """Shutdown the VEIL4 system"""
        if not self.running:
            return
        
        # Log system shutdown
        self.audit.log_transition(
            agent_id="system",
            operation="system_shutdown",
            from_state={"status": "running"},
            to_state={"status": "stopped"},
            metadata={}
        )
        
        # Unload all plugins
        for plugin_name in list(self.plugins.plugins.keys()):
            self.plugins.unload_plugin(plugin_name)
        
        self.running = False
    
    def register_agent(
        self,
        agent_id: str,
        agent_type: AgentType,
        capabilities: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Register a new agent (human or model) in VEIL4.
        
        Args:
            agent_id: Unique identifier
            agent_type: Type of agent
            capabilities: Initial capabilities to grant
            metadata: Additional metadata
        """
        # Register in parity layer
        agent = self.parity.register_agent(
            agent_id=agent_id,
            agent_type=agent_type,
            capabilities=capabilities or [],
            metadata=metadata
        )
        
        # Log agent registration
        self.audit.log_transition(
            agent_id="system",
            operation="register_agent",
            from_state=None,
            to_state={
                "agent_id": agent_id,
                "agent_type": agent_type.value,
                "capabilities": capabilities or []
            },
            metadata=metadata or {}
        )
        
        return agent
    
    def create_quantum_state(
        self,
        state_id: str,
        states: List[Dict[str, Any]],
        amplitudes: Optional[List[float]] = None
    ) -> str:
        """
        Create a superposition of quantum states.
        
        Args:
            state_id: Identifier for the superposition
            states: List of possible states
            amplitudes: Probability amplitudes
            
        Returns:
            State ID
        """
        # Create superposition
        self.quantum.create_superposition(state_id, states, amplitudes)
        
        # Maintain coherence
        for state in states:
            self.coherence.maintain_coherence(state_id)
        
        # Log creation
        self.audit.log_transition(
            agent_id="system",
            operation="create_superposition",
            from_state=None,
            to_state={"state_id": state_id, "num_states": len(states)},
            metadata={}
        )
        
        return state_id
    
    def observe_quantum_state(
        self,
        state_id: str,
        observer_agent_id: str
    ) -> Dict[str, Any]:
        """
        Observe a quantum state, causing it to collapse.
        
        Args:
            state_id: ID of state to observe
            observer_agent_id: Agent performing the observation
            
        Returns:
            Collapsed state data
        """
        # Observe and collapse
        collapsed = self.quantum.observe(
            state_id,
            observer_context={"observer": observer_agent_id}
        )
        
        # Log observation
        self.audit.log_transition(
            agent_id=observer_agent_id,
            operation="observe_state",
            from_state={"status": "superposed"},
            to_state={"status": "collapsed", "data": collapsed.state_data},
            metadata={"state_id": state_id}
        )
        
        return collapsed.state_data
    
    def grant_capability(
        self,
        resource: str,
        permissions: List[str],
        agent_id: str,
        duration_seconds: Optional[int] = None
    ) -> str:
        """
        Grant a capability to an agent.
        
        Args:
            resource: Resource to grant access to
            permissions: Permissions to grant
            agent_id: Agent receiving capability
            duration_seconds: Validity duration (None = permanent)
            
        Returns:
            Capability token
        """
        duration = timedelta(seconds=duration_seconds) if duration_seconds else None
        
        capability = self.security.issue_capability(
            resource=resource,
            permissions=set(permissions),
            issued_to=agent_id,
            duration=duration,
            delegatable=True
        )
        
        # Log capability grant
        self.audit.log_transition(
            agent_id="system",
            operation="grant_capability",
            from_state=None,
            to_state={
                "resource": resource,
                "permissions": permissions,
                "agent_id": agent_id,
                "token": capability.token
            },
            metadata={}
        )
        
        return capability.token
    
    def verify_access(
        self,
        agent_id: str,
        resource: str,
        permission: str,
        capability_token: str
    ) -> bool:
        """
        Verify an agent has access to a resource.
        
        Args:
            agent_id: Agent requesting access
            resource: Resource being accessed
            permission: Permission required
            capability_token: Capability token to verify
            
        Returns:
            True if access granted
        """
        verified = self.security.verify_capability(
            capability_token,
            resource,
            permission
        )
        
        # Log access attempt
        self.audit.log_transition(
            agent_id=agent_id,
            operation="access_attempt",
            from_state=None,
            to_state={
                "resource": resource,
                "permission": permission,
                "granted": verified
            },
            metadata={"token": capability_token}
        )
        
        return verified
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            "running": self.running,
            "num_agents": len(self.parity.agents),
            "num_plugins": len(self.plugins.plugins),
            "num_superpositions": len(self.quantum.superpositions),
            "num_transitions": len(self.audit.transitions),
            "coherence_states": len(self.coherence.coherent_states)
        }
    
    def _setup_default_capabilities(self):
        """Setup default system capabilities"""
        # Default capabilities that can be granted
        pass
    
    def _setup_default_tools(self):
        """Setup default system tools"""
        # Register basic tools available to all agents
        self.tools.register_tool(
            tool_name="echo",
            tool_function=lambda agent_id, message: f"Echo from {agent_id}: {message}",
            description="Echo a message back",
            parameters={"message": {"type": "string", "description": "Message to echo"}}
        )
