import logging

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from db.repositories.advertisements import get_advertisement
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

    return PredictionResponse(is_violation=is_violation, probability=probability)
