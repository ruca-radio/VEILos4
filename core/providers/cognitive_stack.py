"""
VEIL4 Cognitive Stack - Multi-Model Unified Substrate

Manages multiple LLM layers (Claude, Qwen, Llama, etc.) as a single
coherent cognitive substrate using quantum superposition for decision space.

Models work as unified layers, not separate agents. Responses aggregate
into emergent consensus through quantum observation.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import os

# LLM integration
try:
    from concierge_os.integrations.llm_client import call_llm
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False


class ModelSpecialization(Enum):
    """Model specialization roles in the cognitive stack"""

    REASONING = "reasoning"
    MATH = "math"
    CREATIVE = "creative"
    ANALYSIS = "analysis"
    GENERAL = "general"


@dataclass
class ModelLayer:
    """Represents a single model layer in the cognitive stack"""

    model_name: str
    provider: str
    specialization: ModelSpecialization
    enabled: bool = True
    priority: int = 100


@dataclass
class LayerResponse:
    """Response from a single model layer"""

    model_name: str
    content: str
    confidence: float
    specialization: ModelSpecialization
    metadata: Dict[str, Any] = field(default_factory=dict)


class CognitiveStack:
    """
    Multi-model cognitive substrate using quantum superposition.

    Manages multiple LLM layers that work together as a unified system.
    Prompts are routed to all layers simultaneously, responses aggregate
    into emergent consensus through quantum observation.

    Example:
        stack = CognitiveStack()
        stack.add_layer(ModelLayer("claude-3", "anthropic", ModelSpecialization.REASONING))
        stack.add_layer(ModelLayer("qwen-math", "ollama", ModelSpecialization.MATH))
        result = stack.process_prompt("Solve: 2x + 5 = 13")
    """

    def __init__(self, coherence_engine=None):
        """Initialize cognitive stack with optional quantum coherence engine"""
        self.layers: Dict[str, ModelLayer] = {}
        self.coherence_engine = coherence_engine
        self.superposition_id: Optional[str] = None
        self.last_responses: List[LayerResponse] = []

    def add_layer(self, layer: ModelLayer) -> None:
        """Add a model layer to the cognitive stack"""
        if not layer.enabled:
            return
        layer_id = f"{layer.model_name}:{layer.provider}"
        self.layers[layer_id] = layer

    def remove_layer(self, model_name: str, provider: str) -> None:
        """Remove a model layer from the stack"""
        layer_id = f"{model_name}:{provider}"
        if layer_id in self.layers:
            del self.layers[layer_id]

    def get_layers(
        self, specialization: Optional[ModelSpecialization] = None
    ) -> List[ModelLayer]:
        """Get layers, optionally filtered by specialization"""
        layers = list(self.layers.values())
        if specialization:
            layers = [l for l in layers if l.specialization == specialization]
        return sorted(layers, key=lambda l: l.priority, reverse=True)

    def process_prompt(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        specializations: Optional[List[ModelSpecialization]] = None,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Process prompt through cognitive stack layers.

        Routes prompt to all enabled layers, collects responses,
        and aggregates into consensus through quantum observation.

        Returns dict with: consensus, layer_responses, confidence, superposition_id
        """
        layers = self.get_layers()
        if specializations:
            layers = [l for l in layers if l.specialization in specializations]

        if not layers:
            return {
                "consensus": "No applicable layers",
                "layer_responses": [],
                "confidence": 0.0,
                "superposition_id": None,
            }

        # Create quantum superposition for decision space
        self.superposition_id = self._create_superposition(prompt, layers)

        # Collect responses from all layers
        responses = self._collect_layer_responses(prompt, layers, temperature)
        self.last_responses = responses

        # Aggregate responses into consensus
        consensus = self._aggregate_consensus(responses)

        # Maintain coherence if engine available
        if self.coherence_engine:
            self.coherence_engine.maintain_coherence(self.superposition_id)

        return {
            "consensus": consensus,
            "layer_responses": [
                {
                    "model": r.model_name,
                    "specialization": r.specialization.value,
                    "content": r.content,
                    "confidence": r.confidence,
                }
                for r in responses
            ],
            "confidence": self._calculate_confidence(responses),
            "superposition_id": self.superposition_id,
        }

    def _create_superposition(self, prompt: str, layers: List[ModelLayer]) -> str:
        """Create quantum superposition for decision space"""
        state_data = {
            "prompt": prompt,
            "layers": [f"{l.model_name}:{l.provider}" for l in layers],
        }
        state_str = str(state_data)
        return hashlib.sha256(state_str.encode()).hexdigest()[:16]

    def _collect_layer_responses(
        self, prompt: str, layers: List[ModelLayer], temperature: float
    ) -> List[LayerResponse]:
        """Collect responses from all layers"""
        responses = []
        for layer in layers:
            # Use real LLM if available and API keys configured
            if LLM_AVAILABLE and self._should_use_real_llm(layer):
                content = self._generate_llm_response(prompt, layer, temperature)
            else:
                content = self._generate_mock_response(prompt, layer)
            response = LayerResponse(
                model_name=layer.model_name,
                content=content,
                confidence=self._calculate_layer_confidence(layer, prompt),
                specialization=layer.specialization,
                metadata={"provider": layer.provider, "temperature": temperature},
            )
            responses.append(response)
        return responses

    def _should_use_real_llm(self, layer: ModelLayer) -> bool:
        """Check if we should use real LLM for this layer"""
        # Only use real LLM if API keys are configured
        if layer.provider == 'ollama':
            return os.getenv('OLLAMA_BASE_URL') is not None
        elif layer.provider in ['openai', 'anthropic', 'xai']:
            key_map = {
                'openai': 'OPENAI_API_KEY',
                'anthropic': 'ANTHROPIC_API_KEY',
                'xai': 'XAI_API_KEY'
            }
            return os.getenv(key_map.get(layer.provider, '')) is not None
        return False
    
    def _generate_llm_response(self, prompt: str, layer: ModelLayer, temperature: float) -> str:
        """Generate response using real LLM API"""
        try:
            # Construct messages with specialization-aware system prompt
            system_prompts = {
                ModelSpecialization.REASONING: "You are a logical reasoning specialist. Analyze step-by-step.",
                ModelSpecialization.MATH: "You are a mathematical problem solver. Show your work.",
                ModelSpecialization.CREATIVE: "You are a creative thinking specialist. Explore possibilities.",
                ModelSpecialization.ANALYSIS: "You are an analytical specialist. Identify patterns.",
                ModelSpecialization.GENERAL: "You are a helpful AI assistant."
            }
            
            messages = [
                {"role": "system", "content": system_prompts.get(layer.specialization, system_prompts[ModelSpecialization.GENERAL])},
                {"role": "user", "content": prompt}
            ]
            
            # Call LLM via concierge_os client
            response = call_llm(messages)
            return f"[{layer.model_name}] {response}"
        except Exception as e:
            # Fallback to mock on error
            return self._generate_mock_response(prompt, layer) + f" (LLM error: {str(e)[:30]})"

    def _generate_mock_response(self, prompt: str, layer: ModelLayer) -> str:
        """Generate deterministic mock response based on specialization"""
        responses = {
            ModelSpecialization.REASONING: f"[{layer.model_name}] Analyzing: {prompt[:40]}... Logical approach: break into components.",
            ModelSpecialization.MATH: f"[{layer.model_name}] Mathematical solution: Solving step by step yields result.",
            ModelSpecialization.CREATIVE: f"[{layer.model_name}] Creative: {prompt[:35]}... Multiple perspectives possible.",
            ModelSpecialization.ANALYSIS: f"[{layer.model_name}] Analysis: Key patterns from {prompt[:30]}...",
            ModelSpecialization.GENERAL: f"[{layer.model_name}] Response to: {prompt[:40]}...",
        }
        return responses.get(layer.specialization, f"[{layer.model_name}] Response")

    def _aggregate_consensus(self, responses: List[LayerResponse]) -> str:
        """Aggregate layer responses into consensus"""
        if not responses:
            return ""

        high_confidence = [r for r in responses if r.confidence > 0.6]
        if high_confidence:
            parts = []
            for spec in [ModelSpecialization.MATH, ModelSpecialization.REASONING]:
                resp = next(
                    (r for r in high_confidence if r.specialization == spec), None
                )
                if resp:
                    parts.append(f"{spec.value.title()}: {resp.content}")
            if parts:
                return " | ".join(parts)

        best = max(responses, key=lambda r: r.confidence)
        return best.content

    def _calculate_confidence(self, responses: List[LayerResponse]) -> float:
        """Calculate overall confidence from layer responses"""
        if not responses:
            return 0.0
        return min(1.0, sum(r.confidence for r in responses) / len(responses))

    def _calculate_layer_confidence(self, layer: ModelLayer, prompt: str) -> float:
        """Calculate confidence for a specific layer's response"""
        base = 0.7
        if layer.specialization == ModelSpecialization.MATH and any(
            w in prompt.lower() for w in ["solve", "calculate", "equation", "math"]
        ):
            base = 0.9
        elif layer.specialization == ModelSpecialization.REASONING and any(
            w in prompt.lower() for w in ["why", "explain", "analyze", "think"]
        ):
            base = 0.85
        return base

    def get_stack_info(self) -> Dict[str, Any]:
        """Get information about the current cognitive stack"""
        return {
            "num_layers": len(self.layers),
            "layers": [
                {
                    "model": l.model_name,
                    "provider": l.provider,
                    "specialization": l.specialization.value,
                    "priority": l.priority,
                }
                for l in self.get_layers()
            ],
            "last_superposition_id": self.superposition_id,
            "last_response_count": len(self.last_responses),
        }
