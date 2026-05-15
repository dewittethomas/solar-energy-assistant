from fastapi import APIRouter, Depends, HTTPException, Query

from typing import Annotated

from services.prediction_service import PredictionService
from responses.prediction_result import PredictionResult
from services.dependencies import get_prediction_service

router = APIRouter(prefix='/predictions', tags=['predictions'])

PredictionServiceDep = Annotated[PredictionService, Depends(get_prediction_service)]

@router.get(
    '',
    operation_id="predict_solar_yield",
    response_model=PredictionResult
)
async def predict_solar_yield(
    prediction_service: PredictionServiceDep,
    installation_id: str = Query(...),
    start_date: str = Query(...),
    end_date: str = Query(...)
) -> PredictionResult:
    try:
        predictions = prediction_service.predict_solar_yield(
            installation_id=installation_id,
            start_date=start_date,
            end_date=end_date
        )
        return predictions
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")
