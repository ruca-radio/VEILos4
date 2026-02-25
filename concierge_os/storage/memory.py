import json
from pathlib import Path
from typing import Any, Dict

from ..config import USER_JSON_DIR


def user_memory_path(user_id: int) -> Path:
    return USER_JSON_DIR / f"user_{user_id}.json"


def load_user_memory(user_id: int) -> Dict[str, Any]:
    path = user_memory_path(user_id)
    if not path.exists():
        return {"notes": [], "last_good_morning": None}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_user_memory(user_id: int, data: Dict[str, Any]) -> None:
    path = user_memory_path(user_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

