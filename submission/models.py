from geoalchemy2 import Geometry
from datetime import datetime
from sqlalchemy import Column, String, Float, Text, DateTime
from core.models import Base, SoftDeleteMixin


class Submissions(Base, SoftDeleteMixin):
    __tablename__ = "submissions"

    institution_name = Column(String, nullable=False)
    acronym = Column(String, nullable=True)
    country = Column(String, nullable=False)
    city = Column(String, nullable=False)
    address = Column(Text, nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    chapter_name = Column(String, nullable=False)
    percentage_osm_coverage = Column(Float, nullable=False)
    contributor_name = Column(String, nullable=False)
    contributor_email = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    role_in_chapter = Column(String, nullable=True)
    status = Column(String, default="pending", nullable=False)
    geometry = Column(Geometry(geometry_type='MULTIPOLYGON',
                      srid=4326), nullable=False)
    picture_url = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)
