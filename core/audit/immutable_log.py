"""
VEIL4 Audit & Transparency Layer

Provides immutable logging and complete transparency of all system operations.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json


@dataclass
class StateTransition:
    """Represents a state transition in the system"""
    transition_id: str
    timestamp: datetime
    agent_id: str
    operation: str
    from_state: Optional[Dict[str, Any]]
    to_state: Dict[str, Any]
    metadata: Dict[str, Any]
    previous_hash: Optional[str]  # Hash of previous transition (for chaining)
    transition_hash: str  # Hash of this transition


class ImmutableLog:
    """
    Immutable, cryptographically-chained log of all state transitions.
    
    Implements a simplified blockchain-like structure where each
    entry is cryptographically linked to the previous one.
    """
    
    def __init__(self):
        self.transitions: List[StateTransition] = []
        self.transition_index: Dict[str, StateTransition] = {}
        self.agent_transitions: Dict[str, List[str]] = {}  # agent_id -> transition_ids
        
    def log_transition(
        self,
        agent_id: str,
        operation: str,
        from_state: Optional[Dict[str, Any]],
        to_state: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> StateTransition:
        """
        Log a state transition.
        
        Args:
            agent_id: Agent performing the operation
            operation: Name of the operation
            from_state: State before transition (None for creation)
            to_state: State after transition
            metadata: Additional metadata
            
        Returns:
            StateTransition object
        """
        timestamp = datetime.now()
        
        # Get previous hash for chaining
        previous_hash = None
        if self.transitions:
            previous_hash = self.transitions[-1].transition_hash
        
        # Generate transition ID
        transition_id = self._generate_transition_id(agent_id, operation, timestamp)
        
        # Create transition
        transition = StateTransition(
            transition_id=transition_id,
            timestamp=timestamp,
            agent_id=agent_id,
            operation=operation,
            from_state=from_state,
            to_state=to_state,
            metadata=metadata or {},
            previous_hash=previous_hash,
            transition_hash=""  # Will be computed
        )
        
        # Compute hash
        transition.transition_hash = self._compute_hash(transition)
        
        # Add to log
        self.transitions.append(transition)
        self.transition_index[transition_id] = transition
        
        # Index by agent
        if agent_id not in self.agent_transitions:
            self.agent_transitions[agent_id] = []
        self.agent_transitions[agent_id].append(transition_id)
        
        return transition
    
    def get_transition(self, transition_id: str) -> Optional[StateTransition]:
        """Get a specific transition by ID"""
        return self.transition_index.get(transition_id)
    
    def get_agent_history(self, agent_id: str) -> List[StateTransition]:
        """Get all transitions for a specific agent"""
        if agent_id not in self.agent_transitions:
            return []
        
        return [
            self.transition_index[tid]
            for tid in self.agent_transitions[agent_id]
        ]
    
    def get_recent_transitions(self, count: int = 10) -> List[StateTransition]:
        """Get the most recent transitions"""
        return self.transitions[-count:]
    
    def verify_chain(self) -> bool:
        """
        Verify the integrity of the entire chain.
        
        Returns:
            True if chain is valid, False if tampered
        """
        for i, transition in enumerate(self.transitions):
            # Verify hash
            computed_hash = self._compute_hash(transition)
            if computed_hash != transition.transition_hash:
                return False
            
            # Verify chain link
            if i > 0:
                if transition.previous_hash != self.transitions[i-1].transition_hash:
                    return False
        
        return True
    
    def verify_transition(self, transition_id: str) -> bool:
        """
        Verify a specific transition hasn't been tampered with.
        
        Args:
            transition_id: ID of transition to verify
            
        Returns:
            True if valid, False if tampered
        """
        if transition_id not in self.transition_index:
            return False
        
        transition = self.transition_index[transition_id]
        computed_hash = self._compute_hash(transition)
        return computed_hash == transition.transition_hash
    
    def export_log(self) -> List[Dict[str, Any]]:
        """Export the entire log as JSON-serializable data"""
        return [
            {
                "transition_id": t.transition_id,
                "timestamp": t.timestamp.isoformat(),
                "agent_id": t.agent_id,
                "operation": t.operation,
                "from_state": t.from_state,
                "to_state": t.to_state,
                "metadata": t.metadata,
                "previous_hash": t.previous_hash,
                "transition_hash": t.transition_hash
            }
            for t in self.transitions
        ]
    
    def _generate_transition_id(
        self,
        agent_id: str,
        operation: str,
        timestamp: datetime
    ) -> str:
        """Generate a unique transition ID"""
        data = f"{agent_id}:{operation}:{timestamp.isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def _compute_hash(self, transition: StateTransition) -> str:
        """Compute cryptographic hash of a transition"""
        # Create deterministic representation
        data = {
            "transition_id": transition.transition_id,
            "timestamp": transition.timestamp.isoformat(),
            "agent_id": transition.agent_id,
            "operation": transition.operation,
            "from_state": transition.from_state,
            "to_state": transition.to_state,
            "metadata": transition.metadata,
            "previous_hash": transition.previous_hash
        }
        
        # Convert to JSON string (sorted keys for determinism)
        json_str = json.dumps(data, sort_keys=True)
        
        # Compute SHA-256 hash
        return hashlib.sha256(json_str.encode()).hexdigest()


class ProvenanceTracker:
    """
    Tracks provenance of data and operations through the system.
    
    Maintains a graph of causality showing how data flows and
    transforms through the system.
    """
    
    def __init__(self):
        self.provenance_graph: Dict[str, Dict[str, Any]] = {}
        
    def record_provenance(
        self,
        entity_id: str,
        entity_type: str,
        derived_from: Optional[List[str]] = None,
        generated_by: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Record provenance information for an entity.
        
        Args:
            entity_id: Unique identifier for the entity
            entity_type: Type of entity (data, operation, agent, etc.)
            derived_from: List of entity IDs this was derived from
            generated_by: Operation that generated this entity
            metadata: Additional provenance metadata
        """
        self.provenance_graph[entity_id] = {
            "entity_type": entity_type,
            "derived_from": derived_from or [],
            "generated_by": generated_by,
            "metadata": metadata or {},
            "recorded_at": datetime.now().isoformat()
        }
    
    def get_provenance(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get provenance information for an entity"""
        return self.provenance_graph.get(entity_id)
    
    def trace_lineage(self, entity_id: str) -> List[str]:
        """
        Trace the complete lineage of an entity.
        
        Returns:
            List of entity IDs in the lineage chain
        """
        lineage = []
        to_process = [entity_id]
        visited = set()
        
        while to_process:
            current = to_process.pop(0)
            
            if current in visited:
                continue
            
            visited.add(current)
            lineage.append(current)
            
            if current in self.provenance_graph:
                derived_from = self.provenance_graph[current]["derived_from"]
                to_process.extend(derived_from)
        
        return lineage
