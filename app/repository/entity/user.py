from sqlalchemy import Column, Integer, String, Boolean, event
from sqlalchemy.orm import relationship
from app.repository.entity.base import Base, TimestampMixin
from app.service.activity_log_service import (
    receive_after_insert,
    receive_before_update,
    receive_after_update,
    receive_before_delete,
)


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)

    roles = relationship(
        "Role",
        secondary="user_roles",
        lazy="selectin",
    )


event.listens_for(User, "after_insert")(receive_after_insert)
event.listens_for(User, "before_update")(receive_before_update)
event.listens_for(User, "after_update")(receive_after_update)
event.listens_for(User, "before_delete")(receive_before_delete)
