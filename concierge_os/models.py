from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, EmailStr


ChannelType = Literal["email", "sms"]


class User(BaseModel):
    id: int
    display_name: str
    channel: ChannelType
    address: str  # email or phone
    timezone: str
    created_at: datetime


class UserCreate(BaseModel):
    display_name: str
    channel: ChannelType
    address: str
    timezone: str


class StartRequest(BaseModel):
    display_name: str
    channel: ChannelType
    address: str
    timezone: str


class StartResponse(BaseModel):
    user_id: int
    message: str


class HealthResponse(BaseModel):
    status: str
    app: str


class OutgoingMessage(BaseModel):
    user_id: int
    subject: Optional[str] = None
    text: str
    html: Optional[str] = None
    image_path: Optional[str] = None
    audio_path: Optional[str] = None

