# Event-Driven Notification System

A production-grade **Event-Driven Notification System** leveraging **RabbitMQ** and **FastAPI** to showcase industry-standard messaging patterns, built in Python.

## Architecture Overview

```mermaid
graph TD
    Client["API Client"] -->|POST /notify| Publisher["FastAPI Publisher"]
    
    subgraph RabbitMQ Broker
        Publisher -->|Publish| Exchange["Topic Exchange (notification.exchange)"]
        
        Exchange -->|Routing Key| Queue["Main Queue (notification.queue)"]
        Queue -->|Consume| Consumer["Python Consumer Worker"]
        
        Consumer -.->|NACK (Max Retries Exceeded)| DLX["Dead Letter Exchange (notification.dlx)"]
        DLX --> DLQ["Dead Letter Queue (notification.dlq)"]
    end
    
    Consumer --> EmailHandler["Email Delivery"]
    Consumer --> SMSHandler["SMS Delivery"]
    Consumer --> WebhookHandler["Webhook Delivery"]
```

## Features Demonstrated

1. **Pub/Sub Model**: Publishers emit events without knowing who consumes them. Consumers scale independently based on the queue load.
2. **Event Schemas (Pydantic)**: Strong typing and validation on inputs to prevent malformed data.
3. **At-Least-Once Delivery**: Consumers use manual acknowledgments (`basic_ack`) only after successful processing. If a consumer crashes midway, RabbitMQ re-queues the message.
4. **Retry & Exponential Backoff**: Failures increment retry counts. Backoff ensures transient issues (e.g., rate-limiting) get resolved before retrying.
5. **Dead Letter Queue (DLQ)**: Hard failures (like malformed messages, or max retries exceeded) are routed to a specialized queue for manual inspection, preserving the main queue's health.
6. **Dockerized Environment**: The solution is containerized for simple one-command `docker-compose up` setup.

## Project Structure

```text
.
├── docker-compose.yml
├── README.md
├── requirements.txt
├── src
│   ├── common          # Shared utilities (logger, error handlers)
│   ├── config.py       # Configuration and environment variables
│   ├── consumer        # Long-running worker processes
│   │   ├── handlers.py
│   │   └── worker.py   # Pure pika consumer with manual ACK and retries
│   ├── publisher       # FastAPI application
│   │   ├── broker.py   # RabbitMQ connection and publishing logic
│   │   └── main.py     
│   └── schemas.py      # Pydantic data models
└── tests               # Unit and integration test suites
```

## How to Run

### 1. Run via Docker Compose (Recommended)
This will spin up the RabbitMQ broker, the FastAPI publisher, and the Python Consumer.
```bash
docker-compose up -d --build
```

### 2. Verify Services

**FastAPI Swagger UI:** 
Navigate to [http://localhost:8000/docs](http://localhost:8000/docs)

**RabbitMQ Management UI:**
Navigate to [http://localhost:15672](http://localhost:15672)
- Username: `user`
- Password: `password`

### 3. Send a Notification
```bash
curl -X 'POST' \
  'http://localhost:8000/notify' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "type": "email",
  "payload": {
    "to_email": "test@example.com",
    "subject": "Hello",
    "body": "Event driven architecture!"
  }
}'
```

### 4. Check Logs
```bash
# View the consumer logs to see retry logic and ACKing
docker logs -f notification_consumer
```

## Development & Testing

Setup local environment:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Run tests via Pytest:
```bash
PYTHONPATH=. pytest tests/
```
