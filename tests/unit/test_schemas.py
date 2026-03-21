import pytest
from pydantic import ValidationError
from src.schemas import (
    BaseNotification, 
    NotificationType, 
    EmailPayload, 
    SMSPayload, 
    WebhookPayload,
    NotificationRequest
)

def test_email_payload_validation():
    # Valid payload
    payload = EmailPayload(to_email="test@example.com", subject="Hello", body="Test")
    assert payload.to_email == "test@example.com"

    # Missing required field
    with pytest.raises(ValidationError):
        EmailPayload(to_email="test@example.com", subject="Hello")

def test_base_notification_creation():
    payload = {"to_email": "test@example.com", "subject": "Hello", "body": "Test"}
    notification = BaseNotification(type=NotificationType.EMAIL, payload=payload)
    
    # ID should be auto-generated
    assert notification.id is not None
    assert notification.retries == 0
    assert notification.type == NotificationType.EMAIL

def test_invalid_notification_type():
    payload = {"some": "data"}
    with pytest.raises(ValidationError):
        BaseNotification(type="invalid_type", payload=payload)

def test_notification_request():
    req = NotificationRequest(
        type=NotificationType.SMS,
        payload={"phone_number": "+1234567890", "message": "Test SMS"}
    )
    assert req.type == NotificationType.SMS
    assert req.payload["phone_number"] == "+1234567890"
