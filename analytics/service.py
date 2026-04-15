from sqlalchemy.ext.asyncio import AsyncSession
from submission.repository import SubmissionRepository
from university.repository import UniversityRepository
from .schema import Analytics


class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.submission_repo = SubmissionRepository(db)
        self.university_repo = UniversityRepository(db)

    async def get_metrics(self) -> Analytics:
        total_submission = await self.submission_repo.count()
        total_university = await self.university_repo.count()

        return Analytics(
            total_submission=total_submission,
            total_university=total_university,
        )
