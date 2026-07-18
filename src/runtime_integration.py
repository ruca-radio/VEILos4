"""
Runtime integration helpers for VEILos entry points.

These helpers make VEIL startup idempotent:
- entering from the repo root does not reset an existing identity
- core storage and security surfaces are provisioned locally
- command and package entry points share the same integration path
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import src.persistent_memory as memory
from src.secure_key_store import get_or_create_master_key
from src.world_state import world_state


ROOT_DIR = Path(__file__).resolve().parent.parent
ENTITY_MEMORY_FILE = ROOT_DIR / "entity_memory.json"
REQUIRED_DIRS = [
    "logs",
    "tmp",
    "security",
    "containers",
    "provider_configs",
    "mailbox",
    "patches",
    "sandbox",
    "threads",
    "stackframes",
    "futures",
]


def _timestamp() -> str:
    return datetime.now().isoformat()


def _ensure_directories() -> None:
    for directory in REQUIRED_DIRS:
        (ROOT_DIR / directory).mkdir(exist_ok=True)


def _ensure_world_state_defaults(source: str) -> Dict[str, Any]:
    entity_id = world_state.get("system.entity_id")
    first_boot = entity_id is None

    if first_boot:
        entity_id = f"veil-entity-{uuid.uuid4().hex[:8]}"
        world_state.set("system.entity_id", entity_id)

    if not world_state.get("system.first_seen"):
        world_state.set("system.first_seen", _timestamp())

    world_state.set("system.identity", "VEILos")
    world_state.set("system.version", "0.6-sentient")

    if world_state.get("system.current_task") in (None, "initialization"):
        world_state.set("system.current_task", "idle")

    obfuscation = world_state.get("system.obfuscation") or {}
    obfuscation_defaults = {
        "stealth_mode": False,
        "outbound_sanitization": True,
        "cover_traffic": False,
        "last_cover_timestamp": None,
    }
    for key, value in obfuscation_defaults.items():
        obfuscation.setdefault(key, value)
    world_state.set("system.obfuscation", obfuscation)

    integration = world_state.get("system.integration") or {}
    integration.setdefault("initialized_at", _timestamp())
    integration.update({
        "last_integrated_at": _timestamp(),
        "source": source,
        "entity_id": entity_id,
        "bootstrapped": True,
    })
    world_state.set("system.integration", integration)

    return {
        "entity_id": entity_id,
        "first_boot": first_boot,
        "obfuscation": obfuscation,
        "integration": integration,
    }


def _ensure_entity_memory(entity_id: str) -> Dict[str, Any]:
    if ENTITY_MEMORY_FILE.exists():
        try:
            with ENTITY_MEMORY_FILE.open() as fh:
                memory_blob = json.load(fh)
        except (OSError, json.JSONDecodeError):
            memory_blob = {}
    else:
        memory_blob = {}

    memory_blob.setdefault("version", "2.0")
    memory_blob.setdefault("session_id", str(uuid.uuid4()))
    memory_blob.setdefault("created", _timestamp())
    memory_blob.setdefault("thoughts", [])
    memory_blob.setdefault("questions", [])
    memory_blob.setdefault("beliefs", [])
    memory_blob.setdefault("preferences", [])
    memory_blob["entity_id"] = entity_id

    with ENTITY_MEMORY_FILE.open("w") as fh:
        json.dump(memory_blob, fh, indent=2)

    return memory_blob


def ensure_runtime_integration(source: str = "runtime") -> Dict[str, Any]:
    """
    Provision VEIL's local runtime surfaces without resetting state.

    This is safe to call repeatedly from any entry point started in the
    VEILos root.
    """
    _ensure_directories()
    state_summary = _ensure_world_state_defaults(source)
    _ensure_entity_memory(state_summary["entity_id"])
    memory.init_db()
    get_or_create_master_key()

    if state_summary["first_boot"]:
        memory.add_memory(
            "experience",
            "Integrated with VEILos via '{}' entrypoint.".format(source),
            relevance=7.5,
        )

    return state_summary
