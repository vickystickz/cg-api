from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from core.repository import BaseRepository
from .models import University


class UniversityRepository(BaseRepository[University]):
    def __init__(self, db: AsyncSession):
        super().__init__(University, db)

    async def get_by_name(self, name: str) -> Optional[University]:
        return await self.get_one(short_name=name)
