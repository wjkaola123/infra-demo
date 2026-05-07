from sqlalchemy import Column, Integer, String, DateTime, JSON
from app.repository.entity.base import Base, TimestampMixin


class ActivityLog(Base, TimestampMixin):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_user_id = Column(Integer, nullable=False, index=True)
    actor_username = Column(String(50), nullable=False)
    action = Column(String(20), nullable=False, index=True)  # CREATE / UPDATE / DELETE
    resource_type = Column(String(20), nullable=False, index=True)  # user / role / permission
    resource_id = Column(Integer, nullable=False, index=True)
    old_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
