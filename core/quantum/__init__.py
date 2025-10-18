"""VEIL4 Core Quantum Module"""

from .superposition import SuperpositionManager, QuantumState, StateType
from .coherence import CoherenceEngine, CoherenceMetrics

__all__ = [
    'SuperpositionManager',
    'QuantumState',
    'StateType',
    'CoherenceEngine',
    'CoherenceMetrics'
]
