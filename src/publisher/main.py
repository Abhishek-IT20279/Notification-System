from fastapi import FastAPI, HTTPException, status
from src.schemas import NotificationRequest, BaseNotification
from src.publisher.broker import RabbitMQBroker
from src.common.logger import setup_logger
from contextlib import asynccontextmanager

logger = setup_logger("publisher")
broker = RabbitMQBroker()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing RabbitMQ connection...")
    try:
        broker.setup_exchanges_and_queues()
    except Exception as e:
        logger.warning(f"Could not connect to RabbitMQ during startup: {e}. Will retry on publish.")
    yield
    # Shutdown
    logger.info("Closing RabbitMQ connection...")
    try:
        broker.close()
    except:
        pass

app = FastAPI(
    title="Notification System Publisher",
    lifespan=lifespan
)

@app.post("/notify", status_code=status.HTTP_202_ACCEPTED)
async def publish_notification(request: NotificationRequest):
    try:
        # Construct the BaseNotification
        notification = BaseNotification(
            type=request.type,
            payload=request.payload
        )
        # Publish event
        broker.publish(notification)
        logger.info(f"Successfully published notification: {notification.id}")
        return {"status": "accepted", "id": notification.id}
    except Exception as e:
        logger.error(f"Failed to publish notification: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
async def health_check():
    return {"status": "ok"}
