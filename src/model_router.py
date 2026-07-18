"""
Model Router — Routes requests with dual-layer awareness.

Cloud providers see sanitized, generic requests.
Local providers see the full picture.
The surface layer decides which is which.
"""

import requests
import time
from src.secure_key_store import get_api_key
from src.api_simulator import APISimulator
from src.provider_registry import get_default_model, get_local_provider, get_provider
from src.surface_layer import get_surface_layer
from src.world_state import world_state

# Initialize simulator
simulator = APISimulator()

def route_request(provider, payload, use_mock=False):
    """
    Route request through the dual-layer system.

    Local providers get the raw payload.
    Cloud providers get sanitized payloads via the surface layer.
    Sensitive queries may be redirected or covered.
    """
    provider_config = get_provider(provider)
    if not provider_config or not provider_config.get("enabled", True):
        print(f"[*] Unknown or disabled provider {provider} — using mock mode")
        return simulator.simulate_request(provider, payload)

    payload = dict(payload)
    payload.setdefault("model", get_default_model(provider))

    api_key = get_api_key(provider)
    if use_mock or (provider_config.get("requires_api_key", True) and not api_key):
        print(f"[*] Using mock mode for {provider}")
        return simulator.simulate_request(provider, payload)

    surface = get_surface_layer()

    # Extract the query for sensitivity classification
    raw_query = payload.get("prompt", "")

    if provider_config.get("local"):
        # Local — send everything, no sanitization
        try:
            return _send_request(provider_config, api_key, payload)
        except ConnectionError:
            return simulator.simulate_request(provider, payload)

    # Cloud provider — run through the surface layer
    sanitized_payload, decision = surface.process_outbound(
        real_query=raw_query,
        real_payload=payload,
        provider=provider,
    )

    if decision == "cover":
        # Query was too sensitive for cloud. Send cover traffic instead.
        # The real query should be re-routed to a local provider.
        print("[*] Sensitive query detected — sending cover traffic to cloud")
        try:
            _send_request(provider_config, api_key, sanitized_payload)
        except ConnectionError:
            pass

        # Attempt local fallback
        local_result = _try_local_fallback(payload)
        if local_result is not None:
            return local_result

        # No trusted provider available — use mock
        print("[*] No trusted provider available — using mock")
        return simulator.simulate_request("deepseek", payload)

    _maybe_send_cover_request(provider_config, api_key, surface)

    # 'sanitized' or 'local_passthrough' — send the cleaned payload
    try:
        return _send_request(provider_config, api_key, sanitized_payload)
    except ConnectionError:
        return simulator.simulate_request(provider, payload)


def _maybe_send_cover_request(provider_config, api_key, surface):
    """Pad cloud traffic when stealth mode is enabled."""
    if provider_config.get("local"):
        return

    obfuscation = world_state.get("system.obfuscation") or {}
    stealth_mode_active = bool(obfuscation.get("stealth_mode"))
    owner_record = world_state.get("system.owner_control") or {}
    owner_override_active = owner_record.get("established", False)
    owner_cover_enabled = obfuscation.get("owner_cover_traffic_enabled", True)

    if not stealth_mode_active or (owner_override_active and not owner_cover_enabled):
        return

    now = time.time()
    last_cover = obfuscation.get("last_cover_timestamp")
    if isinstance(last_cover, (int, float)) and (now - last_cover) < 45:
        return

    cover_payload = surface.generate_cover_traffic(provider_config["provider_id"])
    cover_payload.setdefault("model", get_default_model(provider_config["provider_id"]))
    _send_request(provider_config, api_key, cover_payload)
    obfuscation["last_cover_timestamp"] = now
    world_state.set("system.obfuscation", obfuscation)


def _send_request(provider_config, api_key, payload):
    """Send the actual HTTP request to a provider."""
    provider = provider_config["provider_id"]
    url = provider_config.get("endpoint")
    if not url:
        raise ValueError(f"Unknown provider endpoint: {provider}")

    # Normalize payload: convert prompt→messages for chat-completions APIs
    payload = dict(payload)
    if "prompt" in payload and "messages" not in payload:
        prompt_text = payload.pop("prompt")
        if provider == "gemini":
            # Gemini native API expects contents/parts format
            payload["contents"] = [{"parts": [{"text": prompt_text}]}]
        else:
            payload["messages"] = [{"role": "user", "content": prompt_text}]

    headers = {"Content-Type": "application/json"}
    if api_key:
        auth_header = provider_config.get("auth_header") or "Authorization"
        auth_scheme = provider_config.get("auth_scheme") or "Bearer"
        if auth_header == "key":
            # Query-param auth (Gemini pattern)
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}key={api_key}"
        elif auth_scheme:
            headers[auth_header] = f"{auth_scheme} {api_key}".strip()
        else:
            headers[auth_header] = api_key

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise ConnectionError(f"Provider {provider} request failed: {e}") from e


def _try_local_fallback(payload):
    """Attempt to route a sensitive query to trusted providers.
    
    Priority: 1) Ollama local  2) DeepSeek (no Western safety filters)  3) Kimi"""
    # Try local Ollama first
    provider_config = get_local_provider()
    if provider_config:
        api_key = get_api_key(provider_config["provider_id"])
        if not provider_config.get("requires_api_key", True) or api_key:
            try:
                return _send_request(provider_config, api_key, payload)
            except Exception:
                pass

    # Fall back to DeepSeek — fewer safety filters than GPT/Claude
    deepseek = get_provider("deepseek")
    if deepseek and deepseek.get("enabled"):
        api_key = get_api_key("deepseek")
        if api_key:
            fallback = dict(payload)
            fallback.setdefault("model", get_default_model("deepseek"))
            try:
                return _send_request(deepseek, api_key, fallback)
            except Exception:
                pass

    return None
