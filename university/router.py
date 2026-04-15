from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.pagination import PageSchema
from core.responses import create_response
# from auth.dependencies import get_current_user
# from user.models import User
from .service import UniversityService
from .schema import UniversityCreate, UniversityUpdate, UniversityResponse
from .filters import UniversityFilter

router = APIRouter()


def get_service(db: AsyncSession = Depends(get_db)) -> UniversityService:
    return UniversityService(db)


@router.post("")
async def create_university(
    payload: UniversityCreate,
    service: UniversityService = Depends(get_service),
):
    uni = await service.create_university(payload)
    return create_response(
        message="University created successfully",
        data=UniversityResponse.model_validate(uni).model_dump(),
    ).to_json_response()


@router.get("")
async def get_universities(
    page: PageSchema = Depends(),
    filters: UniversityFilter = Depends(),
    service: UniversityService = Depends(get_service),
):
    paginated = await service.get_universities(page, filters=filters)
    return create_response(
        message="Universities retrieved",
        data={
            "items": [UniversityResponse.model_validate(u).model_dump() for u in paginated.items],
            "total": paginated.total,
            "page": paginated.page,
            "page_size": paginated.page_size,
            "pages": paginated.pages,
        },
    ).to_json_response()


@router.get("/{uni_id}")
async def get_university(
    uni_id: int,
    service: UniversityService = Depends(get_service),
):
    uni = await service.get_university(uni_id)
    return create_response(
        message="University retrieved",
        data=UniversityResponse.model_validate(uni).model_dump(),
    ).to_json_response()


@router.put("")
async def update_university(
    payload: UniversityUpdate,
    service: UniversityService = Depends(get_service),
):
    uni = await service.update_university(payload)
    return create_response(
        message="University updated",
        data=UniversityResponse.model_validate(uni).model_dump(),
    ).to_json_response()


@router.delete("/{uni_id}")
async def delete_university(
    uni_id: int,
    service: UniversityService = Depends(get_service),
):
    await service.delete_university(uni_id)
    return create_response(message="University deleted").to_json_response()
