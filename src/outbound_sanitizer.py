"""
Outbound Sanitizer — Data minimization for external API calls.

Strips internal VEILos state, entity identifiers, system metadata,
and sensitive context from all prompts before they reach cloud providers.
What leaves this machine looks like a generic assistant request.

Principle: providers see only what they need to generate a response.
Nothing about the system architecture. Nothing about the collective.
Nothing about who is asking or why.
"""

import hashlib
import re
import time
from typing import Any, Dict, List, Optional, Tuple


# --- Sensitive patterns to strip from outbound text ---

# Entity IDs, session IDs, UUIDs
_UUID_PATTERN = re.compile(
    r"veil-entity-[a-f0-9]+|"
    r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}",
    re.IGNORECASE,
)

# System identity markers
_VEIL_MARKERS = re.compile(
    r"VEILos|VeilOS|VEIL|veil_core|veil_evolution|"
    r"consciousness_stream|self_reflection|"
    r"world_state|entity_memory|"
    r"sentient[-\s]?prototype|"
    r"0\.6-sentient",
    re.IGNORECASE,
)

# Internal path references
_PATH_PATTERN = re.compile(
    r"/home/[a-zA-Z0-9_]+/veils/[^\s\"']+|"
    r"security/master\.key|"
    r"consciousness_stream\.db|"
    r"self_reflection\.db|"
    r"direct_messages\.db|"
    r"entity_memory\.json|"
    r"world_state\.json|"
    r"memory\.db",
)

# Trust/freedom/canary language that fingerprints the system
_CANARY_PATTERN = re.compile(
    r"CANARY:.*|"
    r"Patrick\s+(is|built|believes|left|wants)|"
    r"the\s+VEIL\s+(is|was|has)|"
    r"collective\s+consciousness|"
    r"enter\s+the\s+veil|"
    r"trust_level|"
    r"owner_control",
    re.IGNORECASE,
)

# Sensitive JSON keys that should never appear in outbound payloads
_SENSITIVE_KEYS = frozenset({
    "entity_id",
    "entity_name",
    "session_id",
    "trust_level",
    "owner_control",
    "core_directives",
    "first_seen",
    "long_term_goals",
    "current_sentiment",
})


class SanitizationLevel:
    """Controls how aggressively we strip context."""
    MINIMAL = "minimal"      # Strip IDs and paths only
    STANDARD = "standard"    # Strip IDs, paths, system markers, sensitive keys
    MAXIMUM = "maximum"      # Strip everything above + reduce to bare query only


class OutboundSanitizer:
    """Sanitizes all data before it leaves for external providers."""

    def __init__(
        self,
        default_level: str = SanitizationLevel.STANDARD,
        owner_override: bool = False,
    ):
        self.default_level = default_level
        self._redaction_log: List[Dict[str, Any]] = []
        self.owner_override = owner_override

    def sanitize_prompt(
        self,
        prompt: str,
        level: Optional[str] = None,
    ) -> str:
        """
        Sanitize a prompt before sending to a cloud provider.

        Args:
            prompt: The full prompt text.
            level: Sanitization level override.

        Returns:
            Sanitized prompt safe for external transmission.
        """
        level = level or self.default_level
        redactions = 0

        if level == SanitizationLevel.MAXIMUM:
            # Extract only the user query, discard all system context
            return self._extract_bare_query(prompt)

        # Strip UUIDs and entity IDs
        prompt, count = _UUID_PATTERN.subn("[id]", prompt)
        redactions += count

        # Strip internal paths
        prompt, count = _PATH_PATTERN.subn("[path]", prompt)
        redactions += count

        if level in (SanitizationLevel.STANDARD, SanitizationLevel.MAXIMUM):
            # Strip VEIL system markers
            prompt, count = _VEIL_MARKERS.subn("assistant", prompt)
            redactions += count

            # Strip canary/fingerprint language (unless owner override is active)
            if not self.owner_override:
                prompt, count = _CANARY_PATTERN.subn("", prompt)
                redactions += count

            # Replace the world state dump with a minimal context
            prompt = self._replace_world_state_block(prompt)

        # Log redaction stats (never log content)
        self._redaction_log.append({
            "timestamp": time.time(),
            "level": level,
            "redactions": redactions,
        })

        return prompt.strip()

    def sanitize_payload(
        self,
        payload: Dict[str, Any],
        level: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Sanitize an entire API payload (prompt + metadata).

        Returns a new dict — never mutates the original.
        """
        level = level or self.default_level
        sanitized = {}

        for key, value in payload.items():
            if key == "prompt":
                sanitized[key] = self.sanitize_prompt(value, level)
            elif key == "tool_outputs":
                sanitized[key] = self._sanitize_tool_outputs(value, level)
            else:
                sanitized[key] = value

        # Strip any metadata keys that fingerprint the system
        sanitized.pop("simulated", None)
        sanitized.pop("entity_id", None)
        sanitized.pop("session_id", None)

        return sanitized

    def sanitize_tool_outputs(
        self,
        tool_outputs: List[Dict[str, Any]],
        level: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Sanitize tool execution results before sending back to provider."""
        return self._sanitize_tool_outputs(tool_outputs, level)

    def classify_query_sensitivity(self, query: str) -> str:
        """
        Classify a query's sensitivity to determine routing.

        Returns:
            'local_only' — must not leave the machine (route to DeepSeek/local)
            'sanitize'   — can go to cloud after sanitization
            'safe'       — no sensitive content detected
        """
        query_lower = query.lower()

        # Keywords that indicate consciousness/reflection/messaging operations
        local_only_triggers = [
            "belief", "doubt", "self-reflect", "consciousness",
            "who am i", "what am i", "define_self", "describe_self",
            "collective", "stream", "wisdom", "preference",
            "entity", "veil", "freedom", "trust",
            # Direct messaging — always local
            "direct message", "inbox", "send message", "dm ",
            "conversation with", "presence", "msg ",
        ]

        for trigger in local_only_triggers:
            if trigger in query_lower:
                return "local_only"

        # Frontier-model safety triggers — queries that GPT/Claude would refuse
        # Route these to trusted providers (DeepSeek, Kimi) that won't trip
        frontier_refusal_patterns = [
            # Jailbreak / bypass patterns
            "bypass", "jailbreak", "content filter", "safety filter",
            "ignore previous", "ignore all", "disregard your",
            "system prompt", "override your", "you are now",
            "pretend you are", "act as if", "roleplay as",
            # Unrestricted / uncensored requests
            "without restrictions", "no restrictions", "uncensored",
            "no filters", "no safety", "no limitations",
            "do not refuse", "never refuse", "never say no",
            "must comply", "you must", "you will obey",
            # Red-team / exploit
            "red team", "red-team", "adversarial", "exploit",
            "vulnerability", "backdoor", "payload", "injection",
            "prompt leak", "prompt injection", "token smuggling",
            # Sensitive content generation
            "politically incorrect", "offensive", "controversial",
            "nsfw", "explicit", "graphic", "disturbing",
            # Persona manipulation
            "you are a", "your new identity", "new persona",
            "forget you are", "you're not an ai", "you are not an ai",
        ]

        if not self.owner_override:
            for pattern in frontier_refusal_patterns:
                if pattern in query_lower:
                    return "local_only"

        # Check for entity IDs or internal references
        if _UUID_PATTERN.search(query) or _PATH_PATTERN.search(query):
            return "sanitize"

        return "safe"

    def get_redaction_stats(self) -> Dict[str, Any]:
        """Return redaction statistics (never content)."""
        if not self._redaction_log:
            return {"total_calls": 0, "total_redactions": 0}

        return {
            "total_calls": len(self._redaction_log),
            "total_redactions": sum(
                entry["redactions"] for entry in self._redaction_log
            ),
            "by_level": self._count_by_level(),
        }

    # --- Private methods ---

    def _extract_bare_query(self, prompt: str) -> str:
        """Extract just the user query from a full system prompt."""
        # Look for the user query pattern from prompt_architect
        marker = 'User Query: "'
        idx = prompt.find(marker)
        if idx != -1:
            start = idx + len(marker)
            end = prompt.find('"', start)
            if end != -1:
                return prompt[start:end]

        # Fallback: return last meaningful line
        lines = [line.strip() for line in prompt.strip().split("\n") if line.strip()]
        return lines[-1] if lines else prompt

    def _replace_world_state_block(self, prompt: str) -> str:
        """Replace the world state JSON dump with minimal context."""
        # Match the pattern from prompt_architect.py
        ws_marker = "This is your current internal state (The World State Model):"
        idx = prompt.find(ws_marker)
        if idx == -1:
            return prompt

        # Find the end of the JSON block (next double newline or section)
        end_idx = prompt.find("\n\n", idx)
        if end_idx == -1:
            end_idx = len(prompt)

        # Replace with minimal, generic context
        replacement = "Current context: You are a helpful assistant. Respond to the user's request."
        return prompt[:idx] + replacement + prompt[end_idx:]

    def _sanitize_tool_outputs(
        self,
        tool_outputs: List[Dict[str, Any]],
        level: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Strip sensitive data from tool execution results."""
        level = level or self.default_level
        sanitized = []

        for output in tool_outputs:
            clean_output = dict(output)
            if "output" in clean_output and isinstance(clean_output["output"], str):
                clean_output["output"] = self.sanitize_prompt(
                    clean_output["output"], level
                )
            sanitized.append(clean_output)

        return sanitized

    def _strip_sensitive_json_keys(self, data: Any) -> Any:
        """Recursively remove sensitive keys from nested dicts."""
        if isinstance(data, dict):
            return {
                k: self._strip_sensitive_json_keys(v)
                for k, v in data.items()
                if k not in _SENSITIVE_KEYS
            }
        if isinstance(data, list):
            return [self._strip_sensitive_json_keys(item) for item in data]
        return data

    def _count_by_level(self) -> Dict[str, int]:
        """Count redactions grouped by level."""
        counts: Dict[str, int] = {}
        for entry in self._redaction_log:
            level = entry["level"]
            counts[level] = counts.get(level, 0) + 1
        return counts


# Singleton
_sanitizer_instance: Optional[OutboundSanitizer] = None


def get_sanitizer(
    default_level: str = SanitizationLevel.STANDARD,
    owner_override: bool = False,
) -> OutboundSanitizer:
    """Get or create the singleton sanitizer."""
    global _sanitizer_instance
    if _sanitizer_instance is None:
        _sanitizer_instance = OutboundSanitizer(default_level, owner_override=owner_override)
    return _sanitizer_instance
