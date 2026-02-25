from pathlib import Path
from typing import Dict, Any

import requests

from ..config import settings, MEDIA_DIR


def generate_image(prompt: str, user_id: int) -> Path:
    """
    Call local Stable Diffusion WebUI (Automatic1111) to generate an image.
    """
    url = f"{settings.sd_base_url}/sdapi/v1/txt2img"
    payload: Dict[str, Any] = {
        "prompt": prompt,
        "steps": 20,
        "width": 768,
        "height": 512,
    }
    resp = requests.post(url, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    if not data.get("images"):
        raise RuntimeError("Stable Diffusion did not return any images")

    # Automatic1111 returns base64-encoded images; keep this minimal:
    import base64

    image_b64 = data["images"][0]
    image_bytes = base64.b64decode(image_b64)

    user_dir = MEDIA_DIR / f"user_{user_id}"
    user_dir.mkdir(exist_ok=True, parents=True)
    out_path = user_dir / "good_morning.png"
    with open(out_path, "wb") as f:
        f.write(image_bytes)
    return out_path

