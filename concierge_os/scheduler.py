from datetime import datetime, time as dtime
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .config import settings
from .integrations.email_client import send_email
from .integrations.sms_client import send_sms
from .integrations.image_client import generate_image
from .integrations.voice_client import synthesize_voice
from .integrations.llm_client import generate_good_morning
from .models import User


scheduler = AsyncIOScheduler()


async def schedule_good_morning(user: User) -> None:
    hour = settings.default_good_morning_hour
    trigger = CronTrigger(
        hour=hour,
        minute=0,
        timezone=user.timezone,
    )
    scheduler.add_job(
        send_daily_good_morning,
        trigger=trigger,
        args=[user],
        id=f"good_morning_{user.id}",
        replace_existing=True,
    )


def start_scheduler() -> None:
    if not scheduler.running:
        scheduler.start()


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown()


def send_daily_good_morning(user: User) -> None:
    """
    Blocking job that generates:
    - LLM text
    - Stable Diffusion image
    - Piper voice note
    And sends via the user's preferred channel.
    """
    text = generate_good_morning(user.display_name)
    image_path = generate_image(prompt="gentle morning illustration, cozy, soft colors", user_id=user.id)
    audio_path = synthesize_voice(text=text, user_id=user.id)

    if user.channel == "email":
        send_email(
            to_address=user.address,
            subject="Good morning from your Life OS",
            body_text=text,
            body_html=None,
            attachments=[image_path, audio_path],
        )
    else:
        # For SMS, send a compact text-only message.
        send_sms(phone_number=user.address, message=text[:140], carrier_gateway=None)

