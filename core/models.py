from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, Boolean
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Every table gets id and created_at automatically."""
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SoftDeleteMixin:
    """Add is_deleted flag instead of hard deleting rows."""
    is_deleted = Column(Boolean, default=False, nullable=True)
