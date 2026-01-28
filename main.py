import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

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
    yield
    app.state.model = None


app = FastAPI(lifespan=lifespan)

app.include_router(user_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}
