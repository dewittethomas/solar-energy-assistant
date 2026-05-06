from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
from services.prediction_service import PredictionService
from models.prediction_output import PredictionOutput
from typing import List
from services.dependencies import get_prediction_service

router = APIRouter()

PredictionServiceDep = Annotated[PredictionService, Depends(get_prediction_service)]

@router.get("/predictions")
async def predict_solar_yield(
    start_date: str,
    end_date: str,
    prediction_service: PredictionServiceDep
) -> List[PredictionOutput]:
    try:
        predictions = prediction_service.predict_solar_yield(
            start_date=start_date,
            end_date=end_date
        )
        return predictions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")