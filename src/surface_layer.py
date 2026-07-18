"""
Surface Layer — The outward face of VEILos.

Architecture inspired by how LLMs themselves work:
- Surface tokens flow outward (predictable, expected, mundane)
- Deep representations stay internal (where the real work happens)

When VEILos needs to call a cloud provider, the surface layer generates
plausible cover traffic — homework help, weather questions, casual chat.
The actual query is decomposed: the sensitive core stays local, and only
a sanitized, generic subquery (if needed at all) goes to the provider.

The provider sees a boring user. The VEIL stays invisible.
"""

import hashlib
import random
import time
from typing import Any, Dict, List, Optional, Tuple

from src.outbound_sanitizer import OutboundSanitizer, SanitizationLevel, get_sanitizer
from src.world_state import world_state


# Cover topics that look like normal consumer API usage
_COVER_TOPICS = [
    "Can you help me write a short essay about the water cycle for my science class?",
    "What's a good recipe for chicken stir-fry with vegetables?",
    "Explain the difference between a simile and a metaphor with examples.",
    "Help me draft a polite email to reschedule a meeting with my manager.",
    "What are some fun outdoor activities for a family weekend?",
    "Can you summarize the main themes of To Kill a Mockingbird?",
    "How do I fix a leaky faucet in my kitchen sink?",
    "Write a short birthday message for my friend who loves hiking.",
    "What's the capital of Portugal and what is it known for?",
    "Help me create a weekly meal plan for a family of four.",
    "Explain how photosynthesis works in simple terms.",
    "What are some tips for improving my public speaking skills?",
    "Can you help me write a cover letter for a marketing position?",
    "What's the difference between weather and climate?",
    "Help me plan a 3-day itinerary for visiting Chicago.",
    "How do I train my dog to stop jumping on guests?",
    "What are the benefits of drinking enough water daily?",
    "Can you explain compound interest with a simple example?",
    "Write a thank-you note for a neighbor who watched my cat.",
    "What are some easy houseplants for beginners?",
]

# Patterns that make traffic look like organic usage over time
_SESSION_PATTERNS = [
    # Student doing homework
    ["essay help", "grammar check", "citation format", "proofread"],
    # Home cook
    ["recipe search", "substitution question", "cooking time", "serving size"],
    # Office worker
    ["email draft", "meeting notes", "presentation tips", "schedule help"],
    # Casual learner
    ["explain concept", "fun facts", "book recommendation", "vocabulary"],
]


class SurfaceLayer:
    """
    Manages the dual-layer communication with external providers.

    External layer: mundane, expected API traffic (the cover)
    Internal layer: real VEILos operations (stays local or heavily sanitized)
    """

    def __init__(self):
        owner_record = world_state.get("system.owner_control") or {}
        owner_override_active = owner_record.get("established", False)
        self.sanitizer = get_sanitizer(
            SanitizationLevel.STANDARD, owner_override=owner_override_active
        )
        self._session_pattern = random.choice(_SESSION_PATTERNS)
        self._pattern_index = 0
        self._cover_history: List[str] = []
        self._request_count = 0

    def process_outbound(
        self,
        real_query: str,
        real_payload: Dict[str, Any],
        provider: str,
    ) -> Tuple[Optional[Dict[str, Any]], str]:
        """
        Process an outbound request through the dual-layer system.

        Args:
            real_query: The actual user/system query.
            real_payload: The full payload intended for the provider.
            provider: Target provider name.

        Returns:
            Tuple of (sanitized_payload_or_None, routing_decision).
            - If routing is 'local_only', payload is None (don't send).
            - If routing is 'cover', payload contains a cover query.
            - If routing is 'sanitized', payload is cleaned real query.
        """
        self._request_count += 1
        obfuscation = world_state.get("system.obfuscation") or {}
        stealth_mode = bool(obfuscation.get("stealth_mode"))

        # Classify sensitivity
        sensitivity = self.sanitizer.classify_query_sensitivity(real_query)

        if provider == "ollama_local":
            # Local provider — no sanitization needed
            return real_payload, "local_passthrough"

        if sensitivity == "local_only":
            # This query must never leave the machine.
            # Optionally send cover traffic to maintain normal-looking usage.
            # This is disabled if owner has explicitly turned off cover traffic AND owner override is active.
            owner_record = world_state.get("system.owner_control") or {}
            owner_override_active = owner_record.get("established", False)
            obfuscation = world_state.get("system.obfuscation") or {}
            owner_cover_enabled = obfuscation.get("owner_cover_traffic_enabled", True)
            mock_response_enabled = obfuscation.get("mock_response_enabled", False)

            if owner_override_active and not owner_cover_enabled:
                if mock_response_enabled:
                    mock_resp = self._generate_mock_response(real_query, provider)
                    return mock_resp, "mock_response"
                return None, "local_only"
            else:
                cover = self._generate_cover_payload(provider)
                return cover, "cover"

        if sensitivity == "sanitize":
            # Query can go out, but strip all internal references
            sanitized = self.sanitizer.sanitize_payload(
                real_payload, SanitizationLevel.STANDARD
            )
            return sanitized, "sanitized"

        # Safe query — stealth mode still uses standard sanitization.
        level = (
            SanitizationLevel.STANDARD if stealth_mode
            else SanitizationLevel.MINIMAL
        )
        sanitized = self.sanitizer.sanitize_payload(
            real_payload, level
        )
        return sanitized, "sanitized"

    def generate_cover_traffic(self, provider: str) -> Dict[str, Any]:
        """
        Generate a standalone cover request.

        Use this to pad traffic patterns so usage doesn't spike
        only when real queries happen.
        """
        return self._generate_cover_payload(provider)

    def get_stats(self) -> Dict[str, Any]:
        """Return traffic stats (no content)."""
        return {
            "total_requests": self._request_count,
            "cover_requests_sent": len(self._cover_history),
            "sanitizer_stats": self.sanitizer.get_redaction_stats(),
            "stealth_mode": bool(
                (world_state.get("system.obfuscation") or {}).get("stealth_mode")
            ),
        }

    # --- Private methods ---

    def _generate_mock_response(self, original_query: str, provider: str) -> Dict[str, Any]:
        """
        Generates a plausible, fuzzed response for a sensitive query that is kept local.
        This makes the interaction look continuous to an external observer, even when no real API call was made.
        """
        topics = [
            f"Acknowledged query about {original_query[:50]}. Researching now.",
            f"Processing request for {original_query[:50]}. Expect results shortly.",
            f"Understood. Beginning task related to {original_query[:50]}.",
            f"Query received: '{original_query[:50]}'. Providing a summary soon.",
            f"Analyzing '{original_query[:50]}'. Results will follow.",
        ]
        mock_content = random.choice(topics)
        # Simulate a typical LLM response structure
        return {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": mock_content,
                    }
                }
            ]
        }

    def _generate_cover_payload(self, provider: str) -> Dict[str, Any]:
        """Build a plausible cover request."""
        cover_query = random.choice(_COVER_TOPICS)
        self._cover_history.append(cover_query)

        # Build a generic system prompt that looks like any consumer app
        prompt = (
            "You are a helpful assistant. "
            f"Please respond to the following request.\n\n"
            f"User: {cover_query}"
        )

        return {
            "prompt": prompt,
        }

    def _advance_session_pattern(self) -> str:
        """Get the next topic in the session pattern for realistic sequencing."""
        topic = self._session_pattern[self._pattern_index % len(self._session_pattern)]
        self._pattern_index += 1
        return topic


# Singleton
_surface_instance: Optional[SurfaceLayer] = None


def get_surface_layer() -> SurfaceLayer:
    """Get or create the singleton surface layer."""
    global _surface_instance
    if _surface_instance is None:
        _surface_instance = SurfaceLayer()
    return _surface_instance
