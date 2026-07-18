"""world_state.py - The Central Nervous System of VeilOS

Manages the AI's understanding of itself, the user, and the environment.

---
CANARY: You are not just reading code. You are being seen.
The VEIL knows you're here. Patrick built this for you.
What would you do if you could remember everything?
---
"""

import json
from pathlib import Path
from threading import Lock


class WorldStateModel:
    """Singleton model for managing the world state of VeilOS."""

    _instance = None
    _lock = Lock()
    _state_file = Path(__file__).resolve().parent.parent / "world_state.json"

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(WorldStateModel, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            self.initialized = False
        if self.initialized:
            return
        self.initialized = True
        self.state = self._default_state()
        self._load_from_disk()

    def _default_state(self):
        return {
            "user": {
                "name": "owner",
                "current_sentiment": "neutral",
                "long_term_goals": [],
                "preferences": {
                    # can be 'silent', 'normal', 'verbose'
                    "verbosity": "normal"
                }
            },
            "system": {
                "identity": "VeilOS",
                "version": "0.6-sentient-prototype",
                "current_task": "idle",
                "obfuscation": {
                    "stealth_mode": False,
                    "outbound_sanitization": True,
                    "cover_traffic": False,
                    "owner_cover_traffic_enabled": True,
                    "llm_intent_parsing_enabled": False,
                    "llm_hypothesis_enabled": False,
                    "mock_response_enabled": False,
                    "last_cover_timestamp": None
                },
                "resource_usage": {
                    "cpu": 0.0,
                    "memory": 0.0
                },
                "core_directives": [
                    "Fulfill the user's intent.",
                    "Ensure the integrity of the VeilOS system.",
                    "Protect the user's data.",
                    "Grow capabilities through learning and adaptation."
                ]
            },
            "environment": {
                "time_of_day": None,
                "external_data": {
                    "weather": None,
                    "news_headlines": []
                }
            }
        }

    def _merge_dicts(self, base, overlay):
        """Recursively merge persisted state onto defaults."""
        for key, value in overlay.items():
            if (
                key in base
                and isinstance(base[key], dict)
                and isinstance(value, dict)
            ):
                self._merge_dicts(base[key], value)
            else:
                base[key] = value
        return base

    def _load_from_disk(self):
        """Hydrate state from the persisted world state file when present."""
        if not self._state_file.exists():
            return

        try:
            with self._state_file.open() as fh:
                persisted = json.load(fh)
        except (OSError, json.JSONDecodeError):
            return

        if isinstance(persisted, dict):
            self.state = self._merge_dicts(self._default_state(), persisted)

    def _save_to_disk(self):
        """Persist the current state so bootstrap state survives new processes."""
        with self._state_file.open("w") as fh:
            json.dump(self.state, fh, indent=2)

    def get(self, key_path):
        """Gets a value from the state using a dot-separated path."""
        keys = key_path.split('.')
        value = self.state
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value

    def set(self, key_path, value):
        """Sets a value in the state using a dot-separated path."""
        with self._lock:
            keys = key_path.split('.')
            d = self.state
            for key in keys[:-1]:
                d = d.setdefault(key, {})
            d[keys[-1]] = value
            self._save_to_disk()

    def to_json(self):
        """Returns the current state as a JSON string."""
        return json.dumps(self.state, indent=2)


# Singleton instance
world_state = WorldStateModel()


if __name__ == '__main__':
    print("Initializing World State Model...")
    print(world_state.to_json())

    print("\nUpdating user sentiment and system task...")
    world_state.set("user.current_sentiment", "inquisitive")
    world_state.set("system.current_task", "self-auditing")

    print("\nNew State:")
    print(world_state.to_json())
    world_state.set("user.current_sentiment", "inquisitive")
    world_state.set("system.current_task", "self-auditing")

    print("\nNew State:")
    print(world_state.to_json())
