import pika
import json
from src.config import settings
from src.common.logger import setup_logger
from src.schemas import BaseNotification

logger = setup_logger("broker")

class RabbitMQBroker:
    def __init__(self):
        self.connection = None
        self.channel = None
        
    def connect(self):
        try:
            parameters = pika.URLParameters(settings.RABBITMQ_URL)
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            logger.info("Connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise
            
    def setup_exchanges_and_queues(self):
        if not self.channel:
            self.connect()
            
        # Declare Dead Letter Exchange and Queue
        self.channel.exchange_declare(
            exchange=settings.DLX_NAME, 
            exchange_type='direct', 
            durable=True
        )
        self.channel.queue_declare(
            queue=settings.DLQ_NAME, 
            durable=True
        )
        self.channel.queue_bind(
            exchange=settings.DLX_NAME, 
            queue=settings.DLQ_NAME, 
            routing_key='dead_letter'
        )

        # Declare Main Exchange and Queue with DLX configuration
        self.channel.exchange_declare(
            exchange=settings.EXCHANGE_NAME, 
            exchange_type='topic', 
            durable=True
        )
        self.channel.queue_declare(
            queue=settings.QUEUE_NAME, 
            durable=True,
            arguments={
                'x-dead-letter-exchange': settings.DLX_NAME,
                'x-dead-letter-routing-key': 'dead_letter'
            }
        )
        # Bind queue to exchange based on routing key (we can use the type as routing key)
        self.channel.queue_bind(
            exchange=settings.EXCHANGE_NAME, 
            queue=settings.QUEUE_NAME, 
            routing_key='notification.#'
        )
        logger.info("Exchanges and queues setup successfully")

    def publish(self, notification: BaseNotification):
        if not self.channel or self.channel.is_closed:
            self.connect()
            
        routing_key = f"notification.{notification.type.value}"
        
        try:
            self.channel.basic_publish(
                exchange=settings.EXCHANGE_NAME,
                routing_key=routing_key,
                body=notification.model_dump_json(),
                properties=pika.BasicProperties(
                    delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE,
                    content_type='application/json'
                )
            )
            logger.debug(f"Published message with routing_key {routing_key}")
        except Exception as e:
            logger.error(f"Error publishing message: {e}")
            raise

    def close(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("RabbitMQ connection closed")
