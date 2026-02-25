import json
import subprocess
import time
from pathlib import Path
from typing import Optional

import requests

from ..config import settings


def start_ngrok(port: int = 8000) -> Optional[str]:
    """
    Start an ngrok tunnel for the given port and return the public URL.
    Requires ngrok binary and (optionally) NGROK_AUTHTOKEN env variable.
    """
    # Spawn ngrok in the background
    args = [settings.ngrok_bin, "http", str(port)]
    env = dict(**dict(), **dict())  # placeholder to emphasize pure subprocess
    if settings.ngrok_authtoken:
        env = {**env, "NGROK_AUTHTOKEN": settings.ngrok_authtoken}

    subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)

    # Poll ngrok API for public URL
    api_url = "http://127.0.0.1:4040/api/tunnels"
    for _ in range(20):
        try:
            resp = requests.get(api_url, timeout=2)
            if resp.status_code == 200:
                data = resp.json()
                for tunnel in data.get("tunnels", []):
                    if tunnel.get("name", "").startswith("command_line"):
                        public_url = tunnel.get("public_url")
                        if public_url:
                            _cache_public_url(public_url)
                            return public_url
        except Exception:
            time.sleep(1)
    return None


def _cache_public_url(url: str) -> None:
    path = Path(settings.public_url_cache_file)
    path.write_text(url, encoding="utf-8")


def get_cached_public_url() -> Optional[str]:
    path = Path(settings.public_url_cache_file)
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8").strip() or None

