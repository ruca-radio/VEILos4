import json
from typing import Dict, Any

from ..integrations.llm_client import call_llm
from .tools import registry


def react_loop(user_message: str) -> str:
    """
    Minimal ReAct-style loop:
    - Ask LLM for a JSON instruction: {"tool": "...", "input": {...}} or {"final": "..."}
    - Execute tool if requested, then return final text.
    """
    system = (
        "You are an orchestrator for a personal concierge OS. "
        "If a tool is needed, respond ONLY with JSON like "
        '{"tool": "tool_name", "input": {...}}. '
        "Otherwise respond with JSON like {'final': 'message to user'}."
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_message},
    ]
    raw = call_llm(messages)
    try:
        parsed: Dict[str, Any] = json.loads(raw)
    except Exception:
        return raw

    if "final" in parsed:
        return str(parsed["final"])

    tool_name = parsed.get("tool")
    tool_input = parsed.get("input", {})
    if not tool_name:
        return raw

    func = registry.get(tool_name)
    result = func(**tool_input)
    return f"Tool {tool_name} executed with result: {result}"

