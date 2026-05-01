from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
