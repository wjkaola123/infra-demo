from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.repository.entity.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    roles = relationship("Role", secondary="user_roles", back_populates="users")