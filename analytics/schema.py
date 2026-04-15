from pydantic import BaseModel


class Analytics(BaseModel):
    total_submission: int
    total_university: int
