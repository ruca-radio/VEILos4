import os
import json
import logging
from typing import Dict, Any, List, Optional

# Dynamic import for OpenAI to allow for conditional usage
try:
    from openai import OpenAI
    OPENAI_CLIENT = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_CLIENT = None
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI client not available. LLM features may be limited.")

logger = logging.getLogger(__name__)

def call_llm(
    messages: List[Dict[str, str]],
    model: str = "gpt-4o-mini",  # Default to a cost-effective model
    temperature: float = 0.7,
    max_tokens: int = 500,
    response_format: Optional[Dict[str, str]] = None,
) -> Optional[str]:
    """
    Calls the OpenAI-compatible LLM with the given messages.

    Args:
        messages: A list of message dictionaries for the LLM.
        model: The model to use for the API call.
        temperature: Sampling temperature for the model.
        max_tokens: Maximum number of tokens in the response.
        response_format: Optional dictionary to specify response format (e.g., {"type": "json_object"})

    Returns:
        The content of the LLM's response, or None if an error occurs.
    """
    if not OPENAI_AVAILABLE or OPENAI_CLIENT is None:
        logger.error("OpenAI client not initialized. Cannot make LLM call.")
        return None

    try:
        # Construct arguments for the API call
        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            kwargs["response_format"] = response_format

        response = OPENAI_CLIENT.chat.completions.create(**kwargs)
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error calling LLM: {e}")
        return None

def parse_llm_json_response(response_content: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Parses a JSON string from an LLM response.

    Args:
        response_content: The string content from the LLM.

    Returns:
        A dictionary if parsing is successful, None otherwise.
    """
    if not response_content:
        return None
    try:
        return json.loads(response_content)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        return None
