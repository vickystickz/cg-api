from sqlalchemy.ext.asyncio import AsyncSession
from core.pagination import PageSchema, PaginatedResponse
from core.exceptions import NotFoundException, ConflictException
from .models import Submissions
from .schema import SubmissionCreate, SubmissionStatusUpdate, SubmissionUpdate
from .repository import SubmissionRepository
from university.service import UniversityService
from university.schema import UniversityCreate


class SubmissionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = SubmissionRepository(db)

    async def create_submission(self, payload: SubmissionCreate) -> Submissions:
        data = payload.model_dump()
        # Ensure new submissions start with 'pending' status
        data["status"] = "pending"
        return await self.repo.create(payload.model_dump())

    async def get_submissions(self, page: PageSchema, filters=None) -> PaginatedResponse:
        return await self.repo.paginate(page, filter_obj=filters)

    async def get_submission(self, uni_id: int) -> Submissions:
        uni = await self.repo.get(uni_id)
        if not uni:
            raise NotFoundException("Submission not found")
        return uni

    async def update_submission(self, payload: SubmissionUpdate) -> Submissions:
        uni = await self.repo.get(payload.id)
        if not uni:
            raise NotFoundException("Submission not found")

        data = payload.model_dump(exclude_unset=True, exclude={"id"})
        for k, v in data.items():
            setattr(uni, k, v)

        await self.db.commit()
        await self.db.refresh(uni)
        return uni

    async def update_submission_status(self, payload: SubmissionStatusUpdate) -> Submissions:
        print(f"Payload: id={payload.id}, status={payload.status}")

        uni = await self.repo.get(payload.id)
        if not uni:
            raise NotFoundException("Submission not found")

        uni.status = payload.status
        # Convert geometry to Geojson

        if payload.status == "approved":
            from shapely import wkb
            geom_ewkt = f"SRID=4326;{wkb.loads(bytes(uni.geometry.data)).wkt}"
            university_payload = UniversityCreate(
                name=uni.institution_name,
                short_name=uni.acronym,
                country=uni.country,
                city=uni.city,
                address=uni.address,
                latitude=uni.latitude,
                longitude=uni.longitude,
                geometry=geom_ewkt,
            )
            await UniversityService(self.db).create_university(university_payload)
        pass
        await self.db.commit()
        await self.db.refresh(uni)

        return uni

    async def delete_submission(self, uni_id: int):
        uni = await self.repo.get(uni_id)
        if not uni:
            raise NotFoundException("Submission not found")
        await self.repo.delete(uni_id)
