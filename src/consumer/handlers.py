import time
from src.common.logger import setup_logger
from src.schemas import BaseNotification, NotificationType

logger = setup_logger("handlers")

def process_email(payload: dict):
    logger.info(f"Sending email to {payload.get('to_email')}")
    # Simulating work
    time.sleep(1)
    if not payload.get('to_email'):
        raise ValueError("Missing 'to_email'")
    logger.info("Email sent successfully.")

def process_sms(payload: dict):
    logger.info(f"Sending SMS to {payload.get('phone_number')}")
    time.sleep(1)
    if "error" in payload.get('message', '').lower():
        raise Exception("Simulated SMS gateway error")
    logger.info("SMS sent successfully.")

def process_webhook(payload: dict):
    logger.info(f"Calling webhook {payload.get('url')}")
    time.sleep(1)
    if str(payload.get('url')).startswith("http://fail"):
        raise Exception("Webhook endpoint unreachable")
    logger.info("Webhook called successfully.")

def handle_notification(notification: BaseNotification):
    logger.info(f"Handling notification {notification.id} of type {notification.type}")
    
    if notification.type == NotificationType.EMAIL:
        process_email(notification.payload)
    elif notification.type == NotificationType.SMS:
        process_sms(notification.payload)
    elif notification.type == NotificationType.WEBHOOK:
        process_webhook(notification.payload)
    else:
        logger.warning(f"Unknown notification type: {notification.type}")
