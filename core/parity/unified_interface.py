"""
VEIL4 Cognitive Parity Layer

Provides a unified interface for both AI models and human users,
ensuring equal capabilities and access.
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum


class AgentType(Enum):
    """Types of agents in the system"""
    HUMAN = "human"
    MODEL = "model"
    HYBRID = "hybrid"
    SYSTEM = "system"


@dataclass
class Agent:
    """Represents an agent (human or model) in the system"""
    agent_id: str
    agent_type: AgentType
    capabilities: List[str]
    metadata: Dict[str, Any]


class ParityInterface:
    """
    Unified interface that provides equal capabilities to all agents.
    
    Both humans and AI models interact through the same API,
    ensuring cognitive parity.
    """
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.capability_registry: Dict[str, Callable] = {}
        
    def register_agent(
        self,
        agent_id: str,
        agent_type: AgentType,
        capabilities: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Agent:
        """
        Register a new agent (human or model) in the system.
        
        Args:
            agent_id: Unique identifier for the agent
            agent_type: Type of agent
            capabilities: List of capabilities this agent has
            metadata: Additional agent metadata
            
        Returns:
            Agent object
        """
        agent = Agent(
            agent_id=agent_id,
            agent_type=agent_type,
            capabilities=capabilities,
            metadata=metadata or {}
        )
        
        self.agents[agent_id] = agent
        return agent
    
    def register_capability(
        self,
        capability_name: str,
        implementation: Callable
    ):
        """
        Register a capability that both humans and models can use.
        
        Args:
            capability_name: Name of the capability
            implementation: Function implementing the capability
        """
        self.capability_registry[capability_name] = implementation
    
    def invoke_capability(
        self,
        agent_id: str,
        capability_name: str,
        *args,
        **kwargs
    ) -> Any:
        """
        Invoke a capability on behalf of an agent.
        
        Args:
            agent_id: Agent invoking the capability
            capability_name: Name of capability to invoke
            *args, **kwargs: Arguments to the capability
            
        Returns:
            Result of capability invocation
        """
        # Verify agent exists
        if agent_id not in self.agents:
            raise ValueError(f"Unknown agent: {agent_id}")
        
        agent = self.agents[agent_id]
        
        # Check if agent has this capability
        if capability_name not in agent.capabilities:
            raise PermissionError(
                f"Agent {agent_id} does not have capability: {capability_name}"
            )
        
        # Check if capability is registered
        if capability_name not in self.capability_registry:
            raise ValueError(f"Unknown capability: {capability_name}")
        
        # Invoke capability
        implementation = self.capability_registry[capability_name]
        return implementation(agent, *args, **kwargs)
    
    def grant_capability(
        self,
        agent_id: str,
        capability_name: str
    ):
        """Grant a capability to an agent"""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            if capability_name not in agent.capabilities:
                agent.capabilities.append(capability_name)
    
    def revoke_capability(
        self,
        agent_id: str,
        capability_name: str
    ):
        """Revoke a capability from an agent"""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            if capability_name in agent.capabilities:
                agent.capabilities.remove(capability_name)
    
    def get_agent_capabilities(self, agent_id: str) -> List[str]:
        """Get list of capabilities for an agent"""
        if agent_id in self.agents:
            return self.agents[agent_id].capabilities.copy()
        return []
    
    def list_agents(
        self,
        agent_type: Optional[AgentType] = None
    ) -> List[Agent]:
        """
        List all registered agents.
        
        Args:
            agent_type: Filter by agent type (None = all)
            
        Returns:
            List of agents
        """
        if agent_type is None:
            return list(self.agents.values())
        
        return [
            agent for agent in self.agents.values()
            if agent.agent_type == agent_type
        ]


class UnifiedToolInterface:
    """
    Provides a unified tool interface for all agents.
    
    Tools are accessible to both humans and models through
    the same interface.
    """
    
    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}
        
    def register_tool(
        self,
        tool_name: str,
        tool_function: Callable,
        description: str,
        parameters: Dict[str, Any]
    ):
        """
        Register a tool that can be used by any agent.
        
        Args:
            tool_name: Name of the tool
            tool_function: Function implementing the tool
            description: Human-readable description
            parameters: Parameter schema
        """
        self.tools[tool_name] = {
            "function": tool_function,
            "description": description,
            "parameters": parameters
        }
    
    def invoke_tool(
        self,
        tool_name: str,
        agent_id: str,
        **kwargs
    ) -> Any:
        """
        Invoke a tool on behalf of an agent.
        
        Args:
            tool_name: Name of tool to invoke
            agent_id: Agent invoking the tool
            **kwargs: Tool parameters
            
        Returns:
            Tool result
        """
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        tool = self.tools[tool_name]
        tool_function = tool["function"]
        
        # Invoke tool with agent context
        return tool_function(agent_id=agent_id, **kwargs)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools"""
        return [
            {
                "name": name,
                "description": tool["description"],
                "parameters": tool["parameters"]
            }
            for name, tool in self.tools.items()
        ]
