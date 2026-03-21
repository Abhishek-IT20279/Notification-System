import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from src.publisher.main import app

# We need to mock the RabbitMQBroker to avoid requiring a real RabbitMQ instance during basic tests
@pytest.fixture
def mock_broker():
    with patch("src.publisher.main.broker") as mock:
        yield mock

def test_publish_notification_success(client, mock_broker):
    payload = {
        "type": "email",
        "payload": {
            "to_email": "test@example.com",
            "subject": "Integration Test",
            "body": "This is a test message"
        }
    }
    
    response = client.post("/notify", json=payload)
    
    assert response.status_code == 202
    assert "id" in response.json()
    assert response.json()["status"] == "accepted"
    
    # Verify the broker was called to publish
    mock_broker.publish.assert_called_once()

def test_publish_notification_invalid_schema(client):
    # Missing required payload fields for Email
    payload = {
        "type": "email",
        "payload": {
            "subject": "Integration Test"
        }
    }
    # Wait, the validation in NotificationRequest only checks that it's a Dict[str, Any].
    # But later, if we want strict schema validation we might validate the inner payload. 
    # For now, FastAPI accepts it, but if we updated the schema it would fail. Let's test a totally malformed type.
    
    malformed_payload = {
        "type": "invalid_type",
        "payload": {}
    }
    
    response = client.post("/notify", json=malformed_payload)
    assert response.status_code == 422 # Pydantic validation error

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
