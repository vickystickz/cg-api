from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel, field_serializer, field_validator
from core.geo_utils import parse_geometry


class SubmissionCreate(BaseModel):
    institution_name: str
    acronym: str
    country: str
    city: str
    address: Optional[str] = None
    latitude: float
    longitude: float
    chapter_name: str
    percentage_osm_coverage: float
    contributor_name: str
    contributor_email: str
    phone_number: str
    role_in_chapter: Optional[str] = None
    geometry: Any

    @field_validator("geometry", mode="before")
    @classmethod
    def normalize_geometry(cls, v):
        if v is None or (isinstance(v, str) and not v.strip()):
            raise ValueError("Geometry is required")
        try:
            return parse_geometry(v)
        except ValueError as e:
            raise ValueError(str(e))


class SubmissionUpdate(BaseModel):
    id: int
    institution_name: Optional[str] = None
    country: Optional[str] = None
    acronym: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    chapter_name: Optional[str] = None
    percentage_osm_coverage: Optional[float] = None
    contributor_name: Optional[str] = None
    contributor_email: Optional[str] = None
    phone_number: Optional[str] = None
    role_in_chapter: Optional[str] = None
    geometry: Optional[Any] = None

    @field_validator("geometry", mode="before")
    @classmethod
    def normalize_geometry(cls, v):
        if v is None or (isinstance(v, str) and not v.strip()):
            return None
        try:
            return parse_geometry(v)
        except ValueError as e:
            raise ValueError(str(e))


class SubmissionStatusUpdate(BaseModel):
    id: int
    status: str

    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, v):
        allowed_statuses = {"pending", "approved", "rejected"}
        if v not in allowed_statuses:
            raise ValueError(
                f"Status must be one of {', '.join(allowed_statuses)}")
        return v.lower()


class SubmissionResponse(BaseModel):
    id: int
    institution_name: str
    acronym: str
    country: str
    city: str
    address: Optional[str] = None
    latitude: float
    longitude: float
    chapter_name: str
    percentage_osm_coverage: float
    contributor_name: str
    contributor_email: str
    phone_number: str
    role_in_chapter: Optional[str] = None
    geometry: Any
    status: str
    created_at: datetime

    @field_serializer("geometry")
    def serialize_geometry(self, value) -> Optional[dict]:
        """Convert WKB/WKT/EWKT from PostGIS into GeoJSON dict."""
        if value is None:
            return None
        try:
            from shapely import wkb, wkt
            from shapely.geometry import mapping

            # GeoAlchemy2 returns a WKBElement — extract the bytes
            if hasattr(value, "desc"):
                geom = wkb.loads(bytes(value.data))
            # Hex WKB string (common from raw queries)
            elif isinstance(value, str) and all(c in "0123456789abcdefABCDEF" for c in value):
                geom = wkb.loads(value, hex=True)
            # EWKT string like "SRID=4326;POLYGON(...)"
            elif isinstance(value, str) and value.upper().startswith("SRID="):
                wkt_part = value.split(";", 1)[1]
                geom = wkt.loads(wkt_part)
            # Plain WKT
            elif isinstance(value, str):
                geom = wkt.loads(value)
            else:
                return None

            return mapping(geom)
        except Exception:
            return None

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        return value.isoformat() if isinstance(value, datetime) else str(value)

    class Config:
        from_attributes = True
