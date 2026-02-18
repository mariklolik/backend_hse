import asyncio
import json
import logging

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from clients.kafka import KAFKA_BOOTSTRAP, MODERATION_TOPIC, send_to_dlq, create_kafka_producer
from db.connection import create_pool, close_pool
from db.repositories.advertisements import get_advertisement
from db.repositories.moderation import update_moderation_result
from ml.features import extract_features
from ml.model import load_model

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5


async def process_message(
    message_value: dict,
    pool,
    model,
    producer: AIOKafkaProducer,
) -> None:
    item_id = message_value["item_id"]

    results = await pool.fetch(
        "SELECT id FROM moderation_results WHERE item_id = $1 AND status = 'pending' ORDER BY id DESC LIMIT 1",
        item_id,
    )
    if not results:
        logger.warning(f"No pending task for item_id={item_id}")
        return

    task_id = results[0]["id"]

    ad = await get_advertisement(pool, item_id)
    if ad is None:
        await update_moderation_result(pool, task_id, "failed", error_message="Advertisement not found")
        await send_to_dlq(producer, message_value, "Advertisement not found")
        return

    features = extract_features(
        ad["is_verified_seller"],
        ad["images_qty"],
        ad["description"],
        ad["category"],
    )

    probability = float(model.predict_proba(features)[0][1])
    is_violation = probability >= 0.5

    await update_moderation_result(
        pool, task_id, "completed",
        is_violation=is_violation,
        probability=probability,
    )
    logger.info(f"Processed item_id={item_id} task_id={task_id} violation={is_violation}")


async def run_worker():
    model = load_model()
    pool = await create_pool()
    producer = await create_kafka_producer()

    consumer = AIOKafkaConsumer(
        MODERATION_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        group_id="moderation-workers",
        auto_offset_reset="earliest",
    )
    await consumer.start()
    logger.info("Worker started, consuming messages...")

    try:
        async for msg in consumer:
            retry_count = 0
            while retry_count < MAX_RETRIES:
                try:
                    await process_message(msg.value, pool, model, producer)
                    break
                except Exception as e:
                    retry_count += 1
                    logger.error(f"Error processing message (attempt {retry_count}): {e}")
                    if retry_count < MAX_RETRIES:
                        await asyncio.sleep(RETRY_DELAY_SECONDS)
                    else:
                        item_id = msg.value.get("item_id")
                        results = await pool.fetch(
                            "SELECT id FROM moderation_results WHERE item_id = $1 AND status = 'pending' ORDER BY id DESC LIMIT 1",
                            item_id,
                        )
                        if results:
                            await update_moderation_result(
                                pool, results[0]["id"], "failed",
                                error_message=str(e),
                            )
                        await send_to_dlq(producer, msg.value, str(e), retry_count)
    finally:
        await consumer.stop()
        await producer.stop()
        await close_pool(pool)


if __name__ == "__main__":
    asyncio.run(run_worker())
