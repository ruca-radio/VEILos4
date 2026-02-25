from typing import List, Dict, Any

import requests

from ..config import settings
from ..personality import load_personality


def call_llm(messages: List[Dict[str, str]]) -> str:
    """
    Simple chat completion wrapper that supports either:
    - Local Ollama
    - Grok-3 via xAI API
    """
    if settings.llm_backend == "grok" and settings.xai_api_key:
        return _call_grok(messages)
    return _call_ollama(messages)


def _call_ollama(messages: List[Dict[str, str]]) -> str:
    url = f"{settings.ollama_base_url}/v1/chat/completions"
    payload: Dict[str, Any] = {
        "model": settings.ollama_model,
        "messages": messages,
        "stream": False,
    }
    resp = requests.post(url, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def _call_grok(messages: List[Dict[str, str]]) -> str:
    headers = {
        "Authorization": f"Bearer {settings.xai_api_key}",
        "Content-Type": "application/json",
    }
    payload: Dict[str, Any] = {
        "model": settings.xai_model,
        "messages": messages,
    }
    resp = requests.post(settings.xai_base_url, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def generate_good_morning(display_name: str) -> str:
    personality = load_personality()
    prompt = personality.get("good_morning_prompt") or (
        "Compose a short, affectionate good-morning note for a neurodivergent "
        "digital nomad. Include one gentle reminder and one supportive affirmation."
    )
    system = (
        "You are an open-source personal life OS for neurodivergent users and "
        "digital nomads. Be kind, low-pressure, and practical."
    )
    messages = [
        {"role": "system", "content": system},
        {
            "role": "user",
            "content": f"User name: {display_name}\n\nTask: {prompt}",
        },
    ]
    return call_llm(messages)

