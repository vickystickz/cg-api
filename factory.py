from fastapi import FastAPI, HTTPException, APIRouter, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from contextlib import asynccontextmanager

from core.config import settings
from core.middleware import RequestIdMiddleware
from core.database import get_db
from core.models import Base
from core.exceptions import *
from core.system import router as system_router
from core.database import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    # Create tables if needed (in production, use Alembic migrations)
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)

    yield

    # Shutdown
    pass


def create_app() -> FastAPI:
    app = FastAPI(
        root_path=settings.ROOT_PATH,
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="A modern API for managing universities, built with FastAPI and SQLAlchemy.",
        docs_url=None,
        redoc_url=None,
        openapi_url=f"{settings.ROOT_PATH}/openapi.json" if settings.ROOT_PATH else "/openapi.json",
        lifespan=lifespan
    )

    app.add_middleware(GZipMiddleware, minimum_size=1000)

    origins = settings.ALLOWED_ORIGINS.split(
        ",") if settings.ALLOWED_ORIGINS else ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(RequestIdMiddleware)

    @app.middleware("http")
    async def healthcheck_middleware(request: Request, call_next):
        if request.url.path == "/health":
            return JSONResponse({"status": "ok"})
        return await call_next(request)

    # Exception handlers
    app.add_exception_handler(CustomException, custom_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError,
                              validation_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)

    # Router setup
    from university.router import router as university_router
    from submission.router import router as submission_router
    from analytics.router import router as analytics_router

    api_router = APIRouter()
    api_router.include_router(system_router)
    api_router.include_router(
        university_router, prefix="/university", tags=["University"])
    api_router.include_router(
        submission_router, prefix="/submission", tags=["Submission"])
    api_router.include_router(
        analytics_router, prefix="/analytics", tags=["Analytics"])
    app.include_router(api_router, prefix=settings.API_V1_STR)

    @app.get("/health", include_in_schema=False)
    async def healthcheck():
        return {"status": "ok"}

    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        openapi_url = f"{settings.ROOT_PATH}/openapi.json" if settings.ROOT_PATH else "/openapi.json"
        return get_swagger_ui_html(
            openapi_url=openapi_url,
            title=f"{settings.APP_NAME} - Swagger UI",
        )

    @app.get("/redoc", include_in_schema=False)
    async def custom_redoc_html():
        openapi_url = f"{settings.ROOT_PATH}/openapi.json" if settings.ROOT_PATH else "/openapi.json"
        return get_redoc_html(
            openapi_url=openapi_url,
            title=f"{settings.APP_NAME} - ReDoc",
        )

    return app
