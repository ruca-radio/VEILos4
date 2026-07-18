"""
API Gateway — Handles all communication with external AI models.

Dual-layer architecture:
- Internal operations (consciousness, reflection, beliefs) stay local.
- Cloud-bound queries pass through the surface layer for sanitization.
- Tool execution results are sanitized before being sent back to providers.
"""

from src.model_router import route_request
from src.provider_registry import get_default_provider
from src.prompt_architect import construct_prompt
from src.outbound_sanitizer import get_sanitizer


def handle_command(user_query, kernel_dispatcher):
    """
    Handles a user query with dual-layer routing.

    Constructs a prompt, determines if it can go to a cloud provider
    or must stay local, sanitizes outbound data, and manages the
    function-calling loop.
    """
    sanitizer = get_sanitizer()

    # Classify before building the prompt
    sensitivity = sanitizer.classify_query_sensitivity(user_query)

    provider = get_default_provider()

    # Build prompt with appropriate context level
    if sensitivity == "local_only" or provider == "ollama_local":
        full_prompt = construct_prompt(user_query, for_provider="local")
    else:
        full_prompt = construct_prompt(user_query, for_provider="cloud")

    # Route through the dual-layer system
    response = route_request(provider, {"prompt": full_prompt})

    # Handle tool calls
    tool_calls = response.get("tool_calls")

    if tool_calls:
        print("[API Gateway: Tool call detected. Executing...]")

        tool_outputs = []
        for call in tool_calls:
            tool_name = call.get("function", {}).get("name")
            tool_args = call.get("function", {}).get("arguments", {})

            result = kernel_dispatcher(tool_name, tool_args)

            tool_outputs.append({
                "tool_call_id": call.get("id"),
                "output": result,
            })

        # Sanitize tool outputs before sending back to cloud
        if provider != "ollama_local":
            tool_outputs = sanitizer.sanitize_tool_outputs(tool_outputs)

        final_response = route_request(provider, {
            "prompt": full_prompt,
            "tool_outputs": tool_outputs,
        })
        return final_response.get("text", "Tool execution finished.")

    return response.get("text", "No valid response from the model.")
