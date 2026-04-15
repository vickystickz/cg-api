from typing import Optional
from pydantic import Field
from core.filters import FilterBase


class UniversityFilter(FilterBase):
    name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    from_date: Optional[str] = Field(None)
    to_date: Optional[str] = Field(None)

    class Constants:
        search_fields = ["name", "short_name", "city", "state"]
