from typing import Optional
from pydantic import Field
from core.filters import FilterBase


class SubmissionFilter(FilterBase):
    institution_name: Optional[str] = None
    short_name: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    from_date: Optional[str] = Field(None)
    to_date: Optional[str] = Field(None)

    class Constants:
        search_fields = ["institution_name", "short_name", "city", "country"]
