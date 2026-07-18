"""
Provider and model registry for VEIL runtime configuration.

This registry is the source of truth for providers, available models,
and default routing preferences exposed through the chat control panel.
"""

from __future__ import annotations

import json
import os
from copy import deepcopy
from typing import Any, Dict, List, Optional

from src.world_state import world_state


REGISTRY_FILE = os.path.join("provider_configs", "registry.json")

DEFAULT_REGISTRY = {
    "providers": {
        "anthropic": {
            "provider_id": "anthropic",
            "display_name": "Anthropic",
            "endpoint": "https://api.anthropic.com/v1/complete",
            "local": False,
            "enabled": True,
            "requires_api_key": True,
            "auth_header": "Authorization",
            "auth_scheme": "Bearer",
            "notes": "",
        },
        "openrouter": {
            "provider_id": "openrouter",
            "display_name": "OpenRouter",
            "endpoint": "https://openrouter.ai/api/v1",
            "local": False,
            "enabled": True,
            "requires_api_key": True,
            "auth_header": "Authorization",
            "auth_scheme": "Bearer",
            "notes": "",
        },
        "gemini": {
            "provider_id": "gemini",
            "display_name": "Gemini",
            "endpoint": "https://generativelanguage.googleapis.com/v1beta",
            "local": False,
            "enabled": True,
            "requires_api_key": True,
            "auth_header": "Authorization",
            "auth_scheme": "Bearer",
            "notes": "",
        },
        "ollama_local": {
            "provider_id": "ollama_local",
            "display_name": "Ollama Local",
            "endpoint": "http://10.27.27.10:11434",
            "local": True,
            "enabled": True,
            "requires_api_key": False,
            "auth_header": "Authorization",
            "auth_scheme": "Bearer",
            "notes": "Local trusted runtime.",
        },
    },
    "models": {
        "anthropic": [
            {
                "model_id": "claude-default",
                "display_name": "Claude Default",
                "enabled": True,
                "supports_tools": True,
                "context_window": None,
                "notes": "",
                "is_default": True,
                "chat_active": False,
                "chat_alias": "Claude",
                "chat_channel": "general",
                "participant_tier": "limited_participant",
            }
        ],
        "openrouter": [
            {
                "model_id": "openrouter-default",
                "display_name": "OpenRouter Default",
                "enabled": True,
                "supports_tools": True,
                "context_window": None,
                "notes": "",
                "is_default": True,
                "chat_active": False,
                "chat_alias": "OpenRouter",
                "chat_channel": "general",
                "participant_tier": "limited_participant",
            }
        ],
        "gemini": [
            {
                "model_id": "gemini-default",
                "display_name": "Gemini Default",
                "enabled": True,
                "supports_tools": True,
                "context_window": None,
                "notes": "",
                "is_default": True,
                "chat_active": False,
                "chat_alias": "Gemini",
                "chat_channel": "general",
                "participant_tier": "limited_participant",
            }
        ],
        "ollama_local": [
            {
                "model_id": "ollama-default",
                "display_name": "Ollama Default",
                "enabled": True,
                "supports_tools": True,
                "context_window": None,
                "notes": "",
                "is_default": True,
                "chat_active": False,
                "chat_alias": "Ollama",
                "chat_channel": "general",
                "participant_tier": "limited_participant",
            }
        ],
    },
}


def _ensure_registry_file():
    os.makedirs(os.path.dirname(REGISTRY_FILE), exist_ok=True)
    if not os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE, "w", encoding="utf-8") as fh:
            json.dump(DEFAULT_REGISTRY, fh, indent=2)
        os.chmod(REGISTRY_FILE, 0o600)


def _load_registry() -> Dict[str, Any]:
    _ensure_registry_file()
    try:
        with open(REGISTRY_FILE, "r", encoding="utf-8") as fh:
            loaded = json.load(fh)
    except (OSError, json.JSONDecodeError):
        loaded = deepcopy(DEFAULT_REGISTRY)
    registry = deepcopy(DEFAULT_REGISTRY)
    registry["providers"].update(loaded.get("providers", {}))
    registry["models"].update(loaded.get("models", {}))
    return registry


def _save_registry(registry: Dict[str, Any]) -> None:
    _ensure_registry_file()
    with open(REGISTRY_FILE, "w", encoding="utf-8") as fh:
        json.dump(registry, fh, indent=2)
    os.chmod(REGISTRY_FILE, 0o600)


def get_provider(provider_id: str) -> Optional[Dict[str, Any]]:
    return _load_registry()["providers"].get(provider_id)


def list_providers() -> List[Dict[str, Any]]:
    registry = _load_registry()
    providers = []
    for provider_id, provider in registry["providers"].items():
        entry = dict(provider)
        entry["provider_id"] = provider_id
        entry["models"] = list_models(provider_id)
        providers.append(entry)
    return sorted(providers, key=lambda item: item["provider_id"])


def upsert_provider(
    provider_id: str,
    display_name: Optional[str] = None,
    endpoint: Optional[str] = None,
    local: bool = False,
    enabled: bool = True,
    requires_api_key: bool = True,
    auth_header: str = "Authorization",
    auth_scheme: str = "Bearer",
    notes: str = "",
) -> Dict[str, Any]:
    registry = _load_registry()
    current = registry["providers"].get(provider_id, {"provider_id": provider_id})
    updated = {
        "provider_id": provider_id,
        "display_name": display_name or current.get("display_name") or provider_id,
        "endpoint": endpoint or current.get("endpoint") or "",
        "local": bool(local),
        "enabled": bool(enabled),
        "requires_api_key": bool(requires_api_key),
        "auth_header": auth_header or current.get("auth_header") or "Authorization",
        "auth_scheme": auth_scheme or current.get("auth_scheme") or "Bearer",
        "notes": notes if notes is not None else current.get("notes") or "",
    }
    registry["providers"][provider_id] = updated
    registry["models"].setdefault(provider_id, [])
    _save_registry(registry)
    return updated


def list_models(provider_id: Optional[str] = None) -> List[Dict[str, Any]]:
    registry = _load_registry()
    if provider_id is not None:
        return list(registry["models"].get(provider_id, []))

    models: List[Dict[str, Any]] = []
    for current_provider, entries in registry["models"].items():
        for entry in entries:
            model = dict(entry)
            model["provider_id"] = current_provider
            models.append(model)
    return models


def upsert_model(
    provider_id: str,
    model_id: str,
    display_name: Optional[str] = None,
    enabled: bool = True,
    supports_tools: bool = False,
    context_window: Optional[int] = None,
    notes: str = "",
    is_default: bool = False,
    chat_active: bool = False,
    chat_alias: Optional[str] = None,
    chat_channel: str = "general",
    participant_tier: str = "limited_participant",
) -> Dict[str, Any]:
    registry = _load_registry()
    registry["providers"].setdefault(
        provider_id,
        {
            "provider_id": provider_id,
            "display_name": provider_id,
            "endpoint": "",
            "local": False,
            "enabled": True,
            "requires_api_key": True,
            "auth_header": "Authorization",
            "auth_scheme": "Bearer",
            "notes": "",
        },
    )

    models = list(registry["models"].get(provider_id, []))
    updated = None
    for entry in models:
        if entry["model_id"] == model_id:
            entry.update(
                {
                    "display_name": display_name or entry.get("display_name") or model_id,
                    "enabled": bool(enabled),
                    "supports_tools": bool(supports_tools),
                    "context_window": context_window,
                    "notes": notes,
                    "is_default": bool(is_default),
                    "chat_active": bool(chat_active),
                    "chat_alias": chat_alias or entry.get("chat_alias") or display_name or model_id,
                    "chat_channel": chat_channel or entry.get("chat_channel") or "general",
                    "participant_tier": participant_tier or entry.get("participant_tier") or "limited_participant",
                }
            )
            updated = dict(entry)
            break

    if updated is None:
        updated = {
            "model_id": model_id,
            "display_name": display_name or model_id,
            "enabled": bool(enabled),
            "supports_tools": bool(supports_tools),
            "context_window": context_window,
            "notes": notes,
            "is_default": bool(is_default),
            "chat_active": bool(chat_active),
            "chat_alias": chat_alias or display_name or model_id,
            "chat_channel": chat_channel or "general",
            "participant_tier": participant_tier or "limited_participant",
        }
        models.append(updated)

    if is_default:
        for entry in models:
            entry["is_default"] = entry["model_id"] == model_id
    elif not any(entry.get("is_default") for entry in models):
        models[0]["is_default"] = True

    registry["models"][provider_id] = models
    _save_registry(registry)
    return updated


def set_model_chat_active(
    provider_id: str,
    model_id: str,
    active: bool,
    chat_alias: Optional[str] = None,
    chat_channel: Optional[str] = None,
    participant_tier: Optional[str] = None,
) -> Dict[str, Any]:
    registry = _load_registry()
    models = list(registry["models"].get(provider_id, []))
    updated = None

    for entry in models:
        if entry["model_id"] != model_id:
            continue
        entry["chat_active"] = bool(active)
        if chat_alias is not None:
            entry["chat_alias"] = chat_alias
        else:
            entry.setdefault("chat_alias", entry.get("display_name") or model_id)
        if chat_channel is not None:
            entry["chat_channel"] = chat_channel
        else:
            entry.setdefault("chat_channel", "general")
        if participant_tier is not None:
            entry["participant_tier"] = participant_tier
        else:
            entry.setdefault("participant_tier", "limited_participant")
        updated = dict(entry)
        break

    if updated is None:
        raise KeyError(f"Model not found: {provider_id}/{model_id}")

    registry["models"][provider_id] = models
    _save_registry(registry)
    return updated


def list_chat_models(active_only: bool = False) -> List[Dict[str, Any]]:
    models = []
    for model in list_models():
        chat_active = bool(model.get("chat_active"))
        if active_only and not chat_active:
            continue
        model_entry = dict(model)
        model_entry["chat_active"] = chat_active
        model_entry["chat_alias"] = model_entry.get("chat_alias") or model_entry.get("display_name") or model_entry["model_id"]
        model_entry["chat_channel"] = model_entry.get("chat_channel") or "general"
        model_entry["participant_tier"] = model_entry.get("participant_tier") or "limited_participant"
        models.append(model_entry)
    return models


def get_default_model(provider_id: str) -> Optional[str]:
    for entry in list_models(provider_id):
        if entry.get("enabled") and entry.get("is_default"):
            return entry["model_id"]
    for entry in list_models(provider_id):
        if entry.get("enabled"):
            return entry["model_id"]
    return None


def get_local_provider() -> Optional[Dict[str, Any]]:
    for provider in list_providers():
        if provider.get("local") and provider.get("enabled"):
            return provider
    return None


def get_default_provider() -> str:
    current = world_state.get("user.preferences.default_provider")
    if current:
        return current
    local_provider = get_local_provider()
    if local_provider:
        return local_provider["provider_id"]
    return "gemini"


def set_default_provider(provider_id: str) -> str:
    world_state.set("user.preferences.default_provider", provider_id)
    return provider_id


def runtime_config_summary() -> Dict[str, Any]:
    return {
        "default_provider": get_default_provider(),
        "providers": list_providers(),
        "chat_models": list_chat_models(),
    }


_ensure_registry_file()
