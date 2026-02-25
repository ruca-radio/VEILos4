"""
VEIL4 Quantum Substrate - State Superposition Manager

Manages quantum-inspired state superposition where multiple potential states
coexist until observation causes collapse to a single state.
"""

from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass
import hashlib
import json
from enum import Enum


class StateType(Enum):
    """Types of quantum states in the system"""
    SUPERPOSED = "superposed"
    COLLAPSED = "collapsed"
    ENTANGLED = "entangled"
    COHERENT = "coherent"


@dataclass
class QuantumState:
    """Represents a quantum-like state with probability amplitude"""
    state_id: str
    state_data: Dict[str, Any]
    amplitude: float  # Probability amplitude (0.0 to 1.0)
    phase: float      # Phase information for interference
    entangled_with: List[str]  # IDs of entangled states
    
    def probability(self) -> float:
        """Calculate probability from amplitude (Born rule)"""
        return self.amplitude ** 2


class SuperpositionManager:
    """
    Manages superposed states in the VEIL4 quantum substrate.
    
    States exist in superposition until an observation is made,
    at which point they collapse to a single definite state.
    """
    
    def __init__(self):
        self.superpositions: Dict[str, List[QuantumState]] = {}
        self.collapsed_states: Dict[str, QuantumState] = {}
        self.observers: Dict[str, List[Callable]] = {}
        
    def create_superposition(
        self,
        superposition_id: str,
        states: List[Dict[str, Any]],
        amplitudes: Optional[List[float]] = None
    ) -> str:
        """
        Create a new superposition of states.
        
        Args:
            superposition_id: Unique identifier for this superposition
            states: List of possible states
            amplitudes: Probability amplitudes (must sum to sqrt(1))
            
        Returns:
            Superposition ID
        """
        if amplitudes is None:
            # Equal superposition
            n = len(states)
            amplitudes = [1.0 / (n ** 0.5)] * n
            
        # Normalize amplitudes
        total_prob = sum(a ** 2 for a in amplitudes)
        if abs(total_prob - 1.0) > 1e-6:
            norm_factor = (1.0 / total_prob) ** 0.5
            amplitudes = [a * norm_factor for a in amplitudes]
        
        quantum_states = []
        for i, (state_data, amplitude) in enumerate(zip(states, amplitudes)):
            state_id = self._generate_state_id(superposition_id, i)
            quantum_states.append(QuantumState(
                state_id=state_id,
                state_data=state_data,
                amplitude=amplitude,
                phase=0.0,
                entangled_with=[]
            ))
            
        self.superpositions[superposition_id] = quantum_states
        return superposition_id
    
    def observe(
        self,
        superposition_id: str,
        observer_context: Optional[Dict[str, Any]] = None
    ) -> QuantumState:
        """
        Observe a superposition, causing it to collapse to a single state.
        
        Args:
            superposition_id: ID of the superposition to observe
            observer_context: Context information about the observer
            
        Returns:
            The collapsed state
        """
        if superposition_id in self.collapsed_states:
            # Already collapsed
            return self.collapsed_states[superposition_id]
            
        if superposition_id not in self.superpositions:
            raise ValueError(f"Unknown superposition: {superposition_id}")
        
        states = self.superpositions[superposition_id]
        
        # Calculate probabilities
        probabilities = [s.probability() for s in states]
        
        # Simulate measurement (collapse to one state)
        import random
        collapsed_state = random.choices(states, weights=probabilities)[0]
        
        # Store collapsed state
        self.collapsed_states[superposition_id] = collapsed_state
        
        # Remove from superpositions
        del self.superpositions[superposition_id]
        
        # Notify observers
        self._notify_observers(superposition_id, collapsed_state, observer_context)
        
        # Handle entangled states
        self._collapse_entangled_states(collapsed_state)
        
        return collapsed_state
    
    def entangle(self, state_id1: str, state_id2: str):
        """Create entanglement between two states"""
        # Find states in superpositions
        for states in self.superpositions.values():
            for state in states:
                if state.state_id == state_id1:
                    state.entangled_with.append(state_id2)
                elif state.state_id == state_id2:
                    state.entangled_with.append(state_id1)
    
    def get_superposition_info(self, superposition_id: str) -> Dict[str, Any]:
        """Get information about a superposition"""
        if superposition_id in self.collapsed_states:
            return {
                "status": "collapsed",
                "state": self.collapsed_states[superposition_id].state_data
            }
            
        if superposition_id not in self.superpositions:
            return {"status": "unknown"}
            
        states = self.superpositions[superposition_id]
        return {
            "status": "superposed",
            "num_states": len(states),
            "states": [
                {
                    "state_id": s.state_id,
                    "probability": s.probability(),
                    "amplitude": s.amplitude,
                    "phase": s.phase,
                    "data": s.state_data
                }
                for s in states
            ]
        }
    
    def register_observer(
        self,
        superposition_id: str,
        callback: Callable[[QuantumState, Optional[Dict]], None]
    ):
        """Register a callback to be notified when a superposition collapses"""
        if superposition_id not in self.observers:
            self.observers[superposition_id] = []
        self.observers[superposition_id].append(callback)
    
    def _generate_state_id(self, superposition_id: str, index: int) -> str:
        """Generate a unique state ID"""
        data = f"{superposition_id}:{index}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def _notify_observers(
        self,
        superposition_id: str,
        collapsed_state: QuantumState,
        context: Optional[Dict[str, Any]]
    ):
        """Notify all registered observers of a collapse"""
        if superposition_id in self.observers:
            for observer in self.observers[superposition_id]:
                observer(collapsed_state, context)
    
    def _collapse_entangled_states(self, collapsed_state: QuantumState):
        """Collapse entangled states (simplified entanglement)"""
        for entangled_id in collapsed_state.entangled_with:
            # Find and collapse entangled states
            for sup_id, states in list(self.superpositions.items()):
                for state in states:
                    if state.state_id == entangled_id:
                        # Collapse this superposition too
                        self.observe(sup_id)
                        break
