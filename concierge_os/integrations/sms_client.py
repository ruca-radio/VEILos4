from typing import Optional

import requests

from ..config import settings
from .email_client import send_email


def send_sms(phone_number: str, message: str, carrier_gateway: Optional[str] = None) -> None:
    """
    Send SMS using either:
    - Textbelt API
    - Email-to-SMS gateway via Gmail
    """
    if settings.sms_backend == "textbelt":
        _send_via_textbelt(phone_number, message)
    else:
        _send_via_email_gateway(phone_number, message, carrier_gateway)


def _send_via_textbelt(phone_number: str, message: str) -> None:
    if not settings.textbelt_api_key:
        raise RuntimeError("TEXTBELT_API_KEY must be set for textbelt backend")
    resp = requests.post(
        settings.textbelt_base_url,
        data={"phone": phone_number, "message": message, "key": settings.textbelt_api_key},
        timeout=15,
    )
    resp.raise_for_status()


def _send_via_email_gateway(phone_number: str, message: str, carrier_gateway: Optional[str]) -> None:
    if not carrier_gateway:
        raise RuntimeError("carrier_gateway is required for email_gateway SMS backend")
    to_address = f"{phone_number}@{carrier_gateway}"
    send_email(
        to_address=to_address,
        subject="",
        body_text=message,
    )

