import logging

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from cache.predictions import get_cached_prediction, set_cached_prediction, delete_cached_prediction
from clients.kafka import send_moderation_request
from db.repositories.advertisements import get_advertisement, close_advertisement, delete_moderation_results_for_item
from db.repositories.moderation import create_moderation_task, get_moderation_result
from ml.features import extract_features

logger = logging.getLogger(__name__)

router = APIRouter()


class PredictionRequest(BaseModel):
    seller_id: int = Field(..., ge=0)
    is_verified_seller: bool
    item_id: int = Field(..., ge=0)
    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    category: int = Field(..., ge=0)
    images_qty: int = Field(..., ge=0)


class PredictionResponse(BaseModel):
    is_violation: bool
    probability: float


class AsyncPredictResponse(BaseModel):
    task_id: int
    status: str
    message: str


class ModerationResultResponse(BaseModel):
    task_id: int
    status: str
    is_violation: bool | None
    probability: float | None


class CloseResponse(BaseModel):
    message: str


@router.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest, req: Request):
    model = req.app.state.model
    if model is None:
        logger.error("Model not available")
        raise HTTPException(status_code=503, detail="Model not available")

    features = extract_features(
        request.is_verified_seller,
        request.images_qty,
        request.description,
        request.category,
    )

    logger.info(
        f"predict request seller_id={request.seller_id} "
        f"item_id={request.item_id} features={features[0].tolist()}"
    )

    probability = model.predict_proba(features)[0][1]
    is_violation = probability >= 0.5

    logger.info(
        f"predict result seller_id={request.seller_id} "
        f"item_id={request.item_id} is_violation={is_violation} "
        f"probability={probability:.4f}"
    )

    return PredictionResponse(is_violation=is_violation, probability=probability)


@router.post("/simple_predict", response_model=PredictionResponse)
async def simple_predict(req: Request, item_id: int = Query(..., ge=0)):
    model = req.app.state.model
    if model is None:
        raise HTTPException(status_code=503, detail="Model not available")

    db_pool = req.app.state.db_pool
    if db_pool is None:
        raise HTTPException(status_code=503, detail="Database not available")

    redis_client = req.app.state.redis_client
    if redis_client is not None:
        cached = await get_cached_prediction(redis_client, item_id)
        if cached is not None:
            return PredictionResponse(**cached)

    ad = await get_advertisement(db_pool, item_id)
    if ad is None:
        raise HTTPException(status_code=404, detail="Advertisement not found")

    features = extract_features(
        ad["is_verified_seller"],
        ad["images_qty"],
        ad["description"],
        ad["category"],
    )

    probability = model.predict_proba(features)[0][1]
    is_violation = probability >= 0.5

    if redis_client is not None:
        await set_cached_prediction(redis_client, item_id, is_violation, float(probability))

    return PredictionResponse(is_violation=is_violation, probability=probability)


@router.post("/async_predict", response_model=AsyncPredictResponse)
async def async_predict(req: Request, item_id: int = Query(..., ge=0)):
    db_pool = req.app.state.db_pool
    if db_pool is None:
        raise HTTPException(status_code=503, detail="Database not available")

    ad = await get_advertisement(db_pool, item_id)
    if ad is None:
        raise HTTPException(status_code=404, detail="Advertisement not found")

    task = await create_moderation_task(db_pool, item_id)

    kafka_producer = req.app.state.kafka_producer
    if kafka_producer is not None:
        await send_moderation_request(kafka_producer, item_id)

    return AsyncPredictResponse(
        task_id=task["id"],
        status="pending",
        message="Moderation request accepted",
    )


@router.get("/moderation_result/{task_id}", response_model=ModerationResultResponse)
async def moderation_result(task_id: int, req: Request):
    db_pool = req.app.state.db_pool
    if db_pool is None:
        raise HTTPException(status_code=503, detail="Database not available")

    result = await get_moderation_result(db_pool, task_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return ModerationResultResponse(
        task_id=result["id"],
        status=result["status"],
        is_violation=result["is_violation"],
        probability=result["probability"],
    )


@router.post("/close", response_model=CloseResponse)
async def close(req: Request, item_id: int = Query(..., ge=0)):
    db_pool = req.app.state.db_pool
    if db_pool is None:
        raise HTTPException(status_code=503, detail="Database not available")

    ad = await get_advertisement(db_pool, item_id)
    if ad is None:
        raise HTTPException(status_code=404, detail="Advertisement not found")

    await delete_moderation_results_for_item(db_pool, item_id)
    await close_advertisement(db_pool, item_id)

    redis_client = req.app.state.redis_client
    if redis_client is not None:
        await delete_cached_prediction(redis_client, item_id)

    return CloseResponse(message="Advertisement closed")
