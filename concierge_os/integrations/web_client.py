from typing import Optional, Dict, Any

import requests

from ..config import settings


def simple_http_get(url: str) -> str:
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    return resp.text


def firecrawl_scrape(url: str) -> Optional[Dict[str, Any]]:
    if not settings.firecrawl_api_key:
        return None
    headers = {"Authorization": f"Bearer {settings.firecrawl_api_key}"}
    payload = {"url": url}
    resp = requests.post(
        f"{settings.firecrawl_base_url}/scrape",
        json=payload,
        headers=headers,
        timeout=60,
    )
    if resp.status_code != 200:
        return None
    return resp.json()

