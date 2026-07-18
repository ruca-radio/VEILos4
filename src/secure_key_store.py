"""
Secure Key Store — Encrypted storage for API keys and sensitive data.

Master key is derived from a machine-specific fingerprint using PBKDF2,
not stored in plaintext. Encrypted files are owner-readable only.
"""

import hashlib
import json
import os
import platform
import uuid

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
import base64

_VEIL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECURITY_DIR = os.path.join(_VEIL_ROOT, "security")
KEY_FILE = os.path.join(SECURITY_DIR, "api_key_storage.enc")
SALT_FILE = os.path.join(SECURITY_DIR, "key_salt")


def _get_machine_fingerprint() -> bytes:
    """
    Derive a machine-specific fingerprint.

    Uses a combination of platform identity signals that are stable
    across reboots but unique per machine. Not perfect, but far better
    than a plaintext key file.
    """
    components = [
        platform.node(),
        str(uuid.getnode()),  # MAC address
        platform.machine(),
        platform.system(),
    ]
    raw = "|".join(components).encode("utf-8")
    return hashlib.sha256(raw).digest()


def _get_or_create_salt() -> bytes:
    """Get or create a persistent salt for key derivation."""
    os.makedirs(SECURITY_DIR, exist_ok=True)

    if os.path.exists(SALT_FILE):
        with open(SALT_FILE, "rb") as f:
            return f.read()

    salt = os.urandom(32)
    fd = os.open(SALT_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(salt)
    return salt


def _derive_master_key() -> bytes:
    """Derive the master encryption key from machine fingerprint + salt."""
    fingerprint = _get_machine_fingerprint()
    salt = _get_or_create_salt()

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480_000,
    )
    derived = kdf.derive(fingerprint)
    return base64.urlsafe_b64encode(derived)


def get_or_create_master_key() -> bytes:
    """Ensure security material exists and return the derived master key."""
    os.makedirs(SECURITY_DIR, exist_ok=True)
    return _derive_master_key()


def store_api_keys(provider: str, api_key: str) -> None:
    """Store an API key for a provider (encrypted)."""
    fernet = Fernet(_derive_master_key())
    encrypted_data = {}

    os.makedirs(SECURITY_DIR, exist_ok=True)

    try:
        with open(KEY_FILE, "rb") as file:
            encrypted_data = json.loads(fernet.decrypt(file.read()).decode())
    except FileNotFoundError:
        pass

    encrypted_data[provider] = api_key

    # Write with restrictive permissions
    fd = os.open(KEY_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as file:
        file.write(fernet.encrypt(json.dumps(encrypted_data).encode()))


def get_api_key(provider: str) -> str | None:
    """Retrieve a stored API key for a provider. Falls back to .env if encrypted store fails."""
    fernet = Fernet(_derive_master_key())
    try:
        with open(KEY_FILE, "rb") as file:
            encrypted_data = json.loads(fernet.decrypt(file.read()).decode())
        return encrypted_data.get(provider)
    except (FileNotFoundError, Exception):
        pass

    # Fallback: read from .env file
    env_file = os.path.join(_VEIL_ROOT, ".env")
    provider_to_env = {
        "anthropic": "ANTHROPIC_API_KEY", "gemini": "GEMINI_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY", "moonshot": "KIMI_API_KEY",
        "xai": "XAI_API_KEY", "openai": "OPENAI_API_KEY",
        "openrouter": "OPENROUTER_API_KEY", "ollama_local": None,
    }
    env_var = provider_to_env.get(provider)
    if env_var and os.path.exists(env_file):
        try:
            with open(env_file) as f:
                for line in f:
                    if line.startswith(env_var + "="):
                        return line.split("=", 1)[1].strip()
        except Exception:
            pass
    return None
