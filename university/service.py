from sqlalchemy.ext.asyncio import AsyncSession
from core.pagination import PageSchema, PaginatedResponse
from core.exceptions import NotFoundException, ConflictException
from .models import University
from .schema import UniversityCreate, UniversityUpdate
from .repository import UniversityRepository


class UniversityService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = UniversityRepository(db)

    async def create_university(self, payload: UniversityCreate) -> University:
        existing = await self.repo.get_by_name(payload.name)
        if existing:
            raise ConflictException("University with this name already exists")

        return await self.repo.create(payload.model_dump())

    async def get_universities(self, page: PageSchema, filters=None) -> PaginatedResponse:
        return await self.repo.paginate(page, filter_obj=filters)

    async def get_university(self, uni_id: int) -> University:
        uni = await self.repo.get(uni_id)
        if not uni:
            raise NotFoundException("University not found")
        return uni

    async def update_university(self, payload: UniversityUpdate) -> University:
        uni = await self.repo.get(payload.id)
        if not uni:
            raise NotFoundException("University not found")

        data = payload.model_dump(exclude_unset=True, exclude={"id"})
        for k, v in data.items():
            setattr(uni, k, v)

        await self.db.commit()
        await self.db.refresh(uni)
        return uni

    async def delete_university(self, uni_id: int):
        uni = await self.repo.get(uni_id)
        if not uni:
            raise NotFoundException("University not found")
        await self.repo.delete(uni_id)
