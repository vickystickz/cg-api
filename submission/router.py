import os
from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.exceptions import BadRequestException
from core.geo_utils import parse_boundary_file
from core.pagination import PageSchema
from core.responses import create_response
from .service import SubmissionService
from .schema import SubmissionCreate, SubmissionStatusUpdate, SubmissionUpdate, SubmissionResponse
from .filters import SubmissionFilter

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {".geojson", ".json", ".kml", ".kmz"}

router = APIRouter()


def get_service(db: AsyncSession = Depends(get_db)) -> SubmissionService:
    return SubmissionService(db)


@router.post("")
async def create_submission(
    payload: SubmissionCreate,
    service: SubmissionService = Depends(get_service),
):
    uni = await service.create_submission(payload)
    return create_response(
        message="Submission created successfully",
        data=SubmissionResponse.model_validate(uni).model_dump(),
    ).to_json_response()


@router.get("")
async def get_submissions(
    page: PageSchema = Depends(),
    filters: SubmissionFilter = Depends(),
    service: SubmissionService = Depends(get_service),
):
    paginated = await service.get_submissions(page, filters=filters)
    return create_response(
        message="Submissions retrieved",
        data={
            "items": [SubmissionResponse.model_validate(u).model_dump() for u in paginated.items],
            "total": paginated.total,
            "page": paginated.page,
            "page_size": paginated.page_size,
            "pages": paginated.pages,
        },
    ).to_json_response()


@router.post("/parse-boundary")
async def parse_boundary(
    file: UploadFile = File(...),
):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise BadRequestException(
            f"Unsupported file type: '{ext}'. Accepted: .geojson, .json, .kml, .kmz"
        )

    content = await file.read()

    if not content:
        raise BadRequestException("Uploaded file is empty.")
    if len(content) > MAX_FILE_SIZE:
        raise BadRequestException("File too large. Maximum size is 10 MB.")

    try:
        geojson = parse_boundary_file(file.filename, content)
    except ValueError as e:
        raise BadRequestException(str(e))

    return create_response(
        message="Boundary parsed successfully",
        data={"geometry": geojson},
    ).to_json_response()


@router.get("/{uni_id}")
async def get_submission(
    uni_id: int,
    service: SubmissionService = Depends(get_service),
):
    uni = await service.get_submission(uni_id)
    return create_response(
        message="Submission retrieved",
        data=SubmissionResponse.model_validate(uni).model_dump(),
    ).to_json_response()


@router.put("")
async def update_submission(
    payload: SubmissionUpdate,
    service: SubmissionService = Depends(get_service),
):
    uni = await service.update_submission(payload)
    return create_response(
        message="Submission Updated",
        data=SubmissionResponse.model_validate(uni).model_dump(),
    ).to_json_response()


@router.put("/status")
async def update_submission_status(
    payload: SubmissionStatusUpdate,
    service: SubmissionService = Depends(get_service),
):
    uni = await service.update_submission_status(payload)
    return create_response(
        message="Submission Status Updated",
        data=SubmissionResponse.model_validate(uni).model_dump(),
    ).to_json_response()


@router.delete("/{uni_id}")
async def delete_submission(
    uni_id: int,
    service: SubmissionService = Depends(get_service),
):
    await service.delete_submission(uni_id)
    return create_response(message="Submission deleted").to_json_response()
