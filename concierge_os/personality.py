from pathlib import Path
from typing import Any, Dict

import yaml

from .config import BASE_DIR


PERSONALITY_PATH = BASE_DIR / "config" / "personality.yaml"


def load_personality() -> Dict[str, Any]:
    if not PERSONALITY_PATH.exists():
        return {
            "name": "NomadNest",
            "tone": "affectionate, neurodivergent-friendly, low-pressure",
            "good_morning_prompt": (
                "Compose a short, affectionate good-morning note for a neurodivergent "
                "digital nomad user. Include one gentle reminder and one supportive affirmation."
            ),
        }

    with open(PERSONALITY_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def reload_personality() -> Dict[str, Any]:
    return load_personality()

