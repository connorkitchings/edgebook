"""
Prediction endpoint.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from vibe_coding.utils.logging import logger

router = APIRouter()


class PredictionRequest(BaseModel):
    """
    Request body for prediction.
    """

    data: list[float]


class PredictionResponse(BaseModel):
    """
    Response body for prediction.
    """

    prediction: float


@router.post("/", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """
    Make a prediction.
    """
    logger.info(f"Received prediction request with data: {request.data}")
    # Add your prediction logic here
    prediction_value = sum(request.data)  # Placeholder prediction
    return PredictionResponse(prediction=prediction_value)
