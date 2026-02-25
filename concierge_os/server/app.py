from fastapi import FastAPI, HTTPException

from ..config import settings
from ..personality import reload_personality
from ..models import StartRequest, StartResponse, HealthResponse
from ..storage.database import init_db, create_user, list_users
from ..scheduler import start_scheduler, schedule_good_morning
from ..integrations.email_client import send_email
from ..integrations.sms_client import send_sms
from ..integrations.tunnel import start_ngrok, get_cached_public_url


app = FastAPI(title=settings.app_name)


@app.on_event("startup")
async def on_startup() -> None:
    init_db()
    start_scheduler()
    public_url = start_ngrok(port=8000)
    if public_url:
        print(f"[ngrok] Public URL: {public_url}")


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", app=settings.app_name)


@app.post("/start", response_model=StartResponse)
async def start_onboarding(req: StartRequest) -> StartResponse:
    user = create_user(
        data=req,
    )
    await schedule_good_morning(user)

    # Send welcome message
    welcome_text = (
        f"Hi {user.display_name} — I’m your open-source personal life OS. "
        "I’ll send you a gentle good-morning check-in every day at 8 AM."
    )
    if user.channel == "email":
        send_email(
            to_address=user.address,
            subject="Welcome to your Life OS",
            body_text=welcome_text,
        )
    else:
        send_sms(phone_number=user.address, message=welcome_text, carrier_gateway=None)

    return StartResponse(user_id=user.id, message="User onboarded successfully.")


@app.post("/admin/reload_personality")
async def admin_reload_personality() -> dict:
    data = reload_personality()
    return {"status": "ok", "personality": data}


@app.get("/admin/public_url")
async def admin_public_url() -> dict:
    url = get_cached_public_url()
    if not url:
        raise HTTPException(status_code=404, detail="No ngrok URL cached")
    return {"public_url": url}

