from typing import Any, Optional
from datetime import datetime
from pydantic import BaseModel, field_serializer, field_validator

from core.geo_utils import parse_geometry


class UniversityCreate(BaseModel):
    name: str
    short_name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "Nigeria"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    website: Optional[str] = None
    description: Optional[str] = None
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


class UniversityUpdate(BaseModel):
    id: int
    name: Optional[str] = None
    short_name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    website: Optional[str] = None
    description: Optional[str] = None
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


class UniversityResponse(BaseModel):
    id: int
    name: str
    short_name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    website: Optional[str] = None
    description: Optional[str] = None
    geometry: Optional[Any]
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
