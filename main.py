import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from clients.kafka import create_kafka_producer
from clients.redis import create_redis_client
from db.connection import create_pool, close_pool
from ml.model import (
    train_model,
    save_model,
    load_model,
    register_model,
    promote_to_production,
    load_from_mlflow,
)
from routers.users import router as user_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)

MODEL_PATH = "model.pkl"
USE_MLFLOW = os.getenv("USE_MLFLOW", "false").lower() == "true"


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not os.path.exists(MODEL_PATH):
        logger.info("Training new model")
        model = train_model()
        save_model(model, MODEL_PATH)
        register_model(model)
        promote_to_production()
        logger.info("Model registered in MLflow")

    if USE_MLFLOW:
        app.state.model = load_from_mlflow()
        logger.info("Model loaded from MLflow")
    else:
        app.state.model = load_model(MODEL_PATH)
        logger.info("Model loaded from pickle")

    try:
        app.state.db_pool = await create_pool()
        logger.info("Database pool created")
    except Exception as e:
        logger.warning(f"Database pool creation failed: {e}")
        app.state.db_pool = None

    try:
        app.state.kafka_producer = await create_kafka_producer()
        logger.info("Kafka producer created")
    except Exception as e:
        logger.warning(f"Kafka producer creation failed: {e}")
        app.state.kafka_producer = None

    try:
        app.state.redis_client = await create_redis_client()
        logger.info("Redis client created")
    except Exception as e:
        logger.warning(f"Redis client creation failed: {e}")
        app.state.redis_client = None

    yield

    if app.state.kafka_producer is not None:
        try:
            await app.state.kafka_producer.stop()
        except Exception:
            pass

    if app.state.redis_client is not None:
        try:
            await app.state.redis_client.aclose()
        except Exception:
            pass

    if app.state.db_pool is not None:
        await close_pool(app.state.db_pool)
    app.state.model = None


app = FastAPI(lifespan=lifespan)

app.include_router(user_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}
