from pathlib import Path
from typing import Callable, Dict, Any

from ..integrations.email_client import send_email
from ..integrations.sms_client import send_sms
from ..integrations.image_client import generate_image
from ..integrations.voice_client import synthesize_voice
from ..integrations.web_client import simple_http_get, firecrawl_scrape


ToolFunc = Callable[..., Any]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, ToolFunc] = {}

    def register(self, name: str, func: ToolFunc) -> None:
        self._tools[name] = func

    def get(self, name: str) -> ToolFunc:
        return self._tools[name]

    def list(self) -> Dict[str, str]:
        return {name: func.__doc__ or "" for name, func in self._tools.items()}


registry = ToolRegistry()


def tool(name: str) -> Callable[[ToolFunc], ToolFunc]:
    def decorator(func: ToolFunc) -> ToolFunc:
        registry.register(name, func)
        return func

    return decorator


@tool("send_email")
def tool_send_email(to_address: str, subject: str, body: str, attachment_paths: list[str] | None = None) -> str:
    """Send an email to a user, optionally with attachments."""
    attachments = [Path(p) for p in (attachment_paths or [])]
    send_email(
        to_address=to_address,
        subject=subject,
        body_text=body,
        body_html=None,
        attachments=attachments,
    )
    return "email_sent"


@tool("send_sms")
def tool_send_sms(phone_number: str, message: str, carrier_gateway: str | None = None) -> str:
    """Send a short SMS message."""
    send_sms(phone_number=phone_number, message=message, carrier_gateway=carrier_gateway)
    return "sms_sent"


@tool("generate_image")
def tool_generate_image(prompt: str, user_id: int) -> str:
    """Generate an image with Stable Diffusion WebUI and return path."""
    path = generate_image(prompt=prompt, user_id=user_id)
    return str(path)


@tool("synthesize_voice")
def tool_synthesize_voice(text: str, user_id: int) -> str:
    """Generate a voice note with Piper TTS and return path."""
    path = synthesize_voice(text=text, user_id=user_id)
    return str(path)


@tool("simple_http_get")
def tool_simple_http_get(url: str) -> str:
    """Fetch HTML content from a URL."""
    return simple_http_get(url)


@tool("firecrawl_scrape")
def tool_firecrawl_scrape(url: str) -> dict | None:
    """Scrape a page via Firecrawl (if configured)."""
    return firecrawl_scrape(url)

