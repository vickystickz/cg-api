from typing import Generic, TypeVar, List
from pydantic import BaseModel, Field

T = TypeVar("T")


class PageSchema(BaseModel):
    page_number: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100,
                           description="Items per page")


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int
