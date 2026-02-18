import json
import os
from datetime import datetime, timezone

from aiokafka import AIOKafkaProducer

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
MODERATION_TOPIC = "moderation"
DLQ_TOPIC = "moderation_dlq"


async def create_kafka_producer() -> AIOKafkaProducer:
    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    await producer.start()
    return producer


async def send_moderation_request(producer: AIOKafkaProducer, item_id: int) -> None:
    message = {
        "item_id": item_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await producer.send_and_wait(MODERATION_TOPIC, message)


async def send_to_dlq(
    producer: AIOKafkaProducer,
    original_message: dict,
    error: str,
    retry_count: int = 1,
) -> None:
    dlq_message = {
        "original_message": original_message,
        "error": error,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "retry_count": retry_count,
    }
    await producer.send_and_wait(DLQ_TOPIC, dlq_message)
