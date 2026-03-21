import pika
import json
import time
from src.config import settings
from src.common.logger import setup_logger
from src.schemas import BaseNotification
from src.consumer.handlers import handle_notification

logger = setup_logger("worker")

class NotificationConsumer:
    def __init__(self):
        self.connection = None
        self.channel = None

    def connect(self):
        while True:
            try:
                parameters = pika.URLParameters(settings.RABBITMQ_URL)
                self.connection = pika.BlockingConnection(parameters)
                self.channel = self.connection.channel()
                
                # Ensure queues exist
                self.setup_queues()
                
                # QoS: fair dispatch
                self.channel.basic_qos(prefetch_count=1)
                
                logger.info("Connected to RabbitMQ and ready to consume.")
                break
            except pika.exceptions.AMQPConnectionError:
                logger.warning("RabbitMQ is not ready yet, retrying in 5 seconds...")
                time.sleep(5)

    def setup_queues(self):
        self.channel.exchange_declare(exchange=settings.DLX_NAME, exchange_type='direct', durable=True)
        self.channel.queue_declare(queue=settings.DLQ_NAME, durable=True)
        self.channel.queue_bind(exchange=settings.DLX_NAME, queue=settings.DLQ_NAME, routing_key='dead_letter')

        self.channel.exchange_declare(exchange=settings.EXCHANGE_NAME, exchange_type='topic', durable=True)
        self.channel.queue_declare(
            queue=settings.QUEUE_NAME, 
            durable=True,
            arguments={
                'x-dead-letter-exchange': settings.DLX_NAME,
                'x-dead-letter-routing-key': 'dead_letter'
            }
        )
        self.channel.queue_bind(exchange=settings.EXCHANGE_NAME, queue=settings.QUEUE_NAME, routing_key='notification.#')

    def publish_retry(self, notification: BaseNotification):
        """Publish the message back to the main queue for retry."""
        routing_key = f"notification.{notification.type.value}"
        self.channel.basic_publish(
            exchange=settings.EXCHANGE_NAME,
            routing_key=routing_key,
            body=notification.model_dump_json(),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE,
                content_type='application/json'
            )
        )

    def process_message(self, ch, method, properties, body):
        try:
            data = json.loads(body)
            notification = BaseNotification(**data)
            logger.info(f"Received message: {notification.id}")
            
            # Application Logic
            handle_notification(notification)
            
            # Manual Acknowledgment (At-least-once delivery)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info(f"Successfully processed and ACKed {notification.id}")
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            
            if 'notification' in locals():
                if notification.retries < settings.MAX_RETRIES:
                    notification.retries += 1
                    logger.info(f"Retrying message {notification.id} (Attempt {notification.retries}/{settings.MAX_RETRIES})")
                    
                    # Exponential backoff (blocking the consumer intentionally for demonstration)
                    delay = (2 ** notification.retries)
                    logger.info(f"Sleeping for {delay} seconds before retry...")
                    time.sleep(delay)
                    
                    # Re-publish and ACK the original message
                    self.publish_retry(notification)
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                else:
                    logger.error(f"Max retries reached for {notification.id}. Sending to DLQ.")
                    # NACK and do NOT requeue -> Goes to DLX -> DLQ
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            else:
                # Malformed message, reject directly
                logger.error("Malformed message, sending to DLQ directly.")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def start(self):
        self.connect()
        self.channel.basic_consume(
            queue=settings.QUEUE_NAME,
            on_message_callback=self.process_message,
            auto_ack=False
        )
        try:
            logger.info("Starting consumer loop. Press CTRL+C to exit.")
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.channel.stop_consuming()
        finally:
            self.connection.close()

if __name__ == "__main__":
    consumer = NotificationConsumer()
    consumer.start()
