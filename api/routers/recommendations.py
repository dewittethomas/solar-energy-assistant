from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from models.recommendation import UsageWindowRecommendationRequest
from responses.recommendation_result import UsageWindowRecommendationResult
from services.dependencies import get_recommendation_service
from services.recommendation_service import RecommendationService

router = APIRouter(prefix='/recommendations', tags=['recommendations'])

RecommendationServiceDep = Annotated[
    RecommendationService,
    Depends(get_recommendation_service)
]

@router.post(
    '/usage-window',
    operation_id='recommend_usage_window',
    response_model=UsageWindowRecommendationResult
)
async def recommend_usage_window(
    request: UsageWindowRecommendationRequest,
    recommendation_service: RecommendationServiceDep
) -> UsageWindowRecommendationResult:
    try:
        return recommendation_service.recommend_usage_window(request)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'Recommendation failed: {str(e)}'
        )
