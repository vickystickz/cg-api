from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.responses import create_response
from .service import AnalyticsService

router = APIRouter()


def get_service(db: AsyncSession = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(db)


@router.get("")
async def get_metrics(
    service: AnalyticsService = Depends(get_service),
):
    metrics = await service.get_metrics()
    return create_response(
        message="Analytics retrieved",
        data=metrics.model_dump(),
    ).to_json_response()
