from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from core.repository import BaseRepository
from .models import Submissions


class SubmissionRepository(BaseRepository[Submissions]):
    def __init__(self, db: AsyncSession):
        super().__init__(Submissions, db)

    async def get_by_contributor_email(self, email: str) -> Optional[Submissions]:
        return await self.get_one(contributor_email=email)
