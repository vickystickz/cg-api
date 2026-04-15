from geoalchemy2 import Geometry
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from core.models import Base, SoftDeleteMixin


class University(Base, SoftDeleteMixin):
    __tablename__ = "universities"

    name = Column(String, nullable=False, index=True)
    short_name = Column(String, nullable=True)       # e.g. "UNILAG"
    address = Column(Text, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    country = Column(String, default="Nigeria")
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    website = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    geometry = Column(Geometry(geometry_type='MULTIPOLYGON',
                      srid=4326), nullable=True)

    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)
