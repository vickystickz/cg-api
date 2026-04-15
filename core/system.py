import datetime
from fastapi import APIRouter
from core.config import settings
from core.responses import create_response

router = APIRouter()


@router.get("/health", tags=["System"], summary="Health Check")
async def health():
    return {
        "status": "ok",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.datetime.now().isoformat()
    }
