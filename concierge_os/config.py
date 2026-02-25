import os
from pathlib import Path
from typing import Optional

from pydantic import BaseSettings, Field


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MEDIA_DIR = DATA_DIR / "media"
USER_JSON_DIR = DATA_DIR / "users"


class Settings(BaseSettings):
    # Core
    app_name: str = "ConciergeOS"
    environment: str = Field("development", env="CONCIERGE_ENV")

    # LLM backends
    llm_backend: str = Field("ollama", env="LLM_BACKEND")  # "ollama" or "grok"
    ollama_base_url: str = Field("http://127.0.0.1:11434", env="OLLAMA_BASE_URL")
    ollama_model: str = Field(
        "llama-3.1-70b-instruct-q5_K_M", env="OLLAMA_MODEL"
    )

    xai_api_key: Optional[str] = Field(None, env="XAI_API_KEY")
    xai_base_url: str = Field("https://api.x.ai/v1/chat/completions", env="XAI_BASE_URL")
    xai_model: str = Field("grok-3", env="XAI_MODEL")

    # Email / Gmail
    gmail_address: Optional[str] = Field(None, env="GMAIL_ADDRESS")
    gmail_app_password: Optional[str] = Field(None, env="GMAIL_APP_PASSWORD")
    gmail_imap_host: str = Field("imap.gmail.com", env="GMAIL_IMAP_HOST")
    gmail_imap_port: int = Field(993, env="GMAIL_IMAP_PORT")

    # SMS
    sms_backend: str = Field("email_gateway", env="SMS_BACKEND")  # "textbelt" or "email_gateway"
    textbelt_api_key: Optional[str] = Field(None, env="TEXTBELT_API_KEY")
    textbelt_base_url: str = Field("https://textbelt.com/text", env="TEXTBELT_BASE_URL")

    # Stable Diffusion WebUI (Automatic1111)
    sd_base_url: str = Field("http://127.0.0.1:7860", env="SD_BASE_URL")

    # TTS / Piper
    piper_binary: str = Field("piper", env="PIPER_BIN")
    piper_voice: str = Field("en_US-libritts_r-medium", env="PIPER_VOICE")

    # Firecrawl (optional)
    firecrawl_api_key: Optional[str] = Field(None, env="FIRECRAWL_API_KEY")
    firecrawl_base_url: str = Field("https://api.firecrawl.dev/v1", env="FIRECRAWL_BASE_URL")

    # Ngrok
    ngrok_bin: str = Field("ngrok", env="NGROK_BIN")
    ngrok_authtoken: Optional[str] = Field(None, env="NGROK_AUTHTOKEN")
    public_url_cache_file: str = str(DATA_DIR / "ngrok_url.txt")

    # Database
    sqlite_path: str = str(DATA_DIR / "concierge.db")

    # Scheduling
    default_good_morning_hour: int = 8

    class Config:
        env_file = ".env"


def ensure_directories() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    MEDIA_DIR.mkdir(exist_ok=True)
    USER_JSON_DIR.mkdir(exist_ok=True)


settings = Settings()
ensure_directories()

