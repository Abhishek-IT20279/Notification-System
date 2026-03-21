from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from enum import Enum
import uuid

class NotificationType(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"

class BaseNotification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: NotificationType
    payload: Dict[str, Any]
    retries: int = 0
    
class EmailPayload(BaseModel):
    to_email: str
    subject: str
    body: str

class SMSPayload(BaseModel):
    phone_number: str
    message: str

class WebhookPayload(BaseModel):
    url: str
    data: Dict[str, Any]

class NotificationRequest(BaseModel):
    type: NotificationType
    payload: Dict[str, Any]
