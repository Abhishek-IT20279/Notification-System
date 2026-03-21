import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Application Settings
    APP_NAME: str = "Notification System"
    APP_VERSION: str = "1.0.0"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # RabbitMQ Settings
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://user:password@localhost:5672/")
    
    # Exchanges and Queues
    EXCHANGE_NAME: str = "notification.exchange"
    QUEUE_NAME: str = "notification.queue"
    DLX_NAME: str = "notification.dlx"
    DLQ_NAME: str = "notification.dlq"
    
    # Retry configurations
    MAX_RETRIES: int = 3
    RETRY_DELAY_MS: int = 5000

settings = Settings()
