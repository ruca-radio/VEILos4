"""
VEIL4 Providers Module

Multi-model cognitive substrate and provider abstractions.
"""

from .cognitive_stack import (
    CognitiveStack,
    ModelLayer,
    ModelSpecialization,
    LayerResponse,
)

__all__ = [
    "CognitiveStack",
    "ModelLayer",
    "ModelSpecialization",
    "LayerResponse",
]
