import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from ml.model import train_model, save_model, load_model
from routers.users import router as user_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)

MODEL_PATH = "model.pkl"


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not os.path.exists(MODEL_PATH):
        logger.info("Training new model")
        model = train_model()
        save_model(model, MODEL_PATH)
    app.state.model = load_model(MODEL_PATH)
    logger.info("Model loaded")
    yield
    app.state.model = None


app = FastAPI(lifespan=lifespan)

app.include_router(user_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}
