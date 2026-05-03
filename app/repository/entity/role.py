from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship
from app.repository.entity.base import Base, TimestampMixin


# 关联表：用户-角色
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    extend_existing=True,
)

# 关联表：角色-权限
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
    extend_existing=True,
)


class Permission(Base, TimestampMixin):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(String(255), nullable=True)

    # Relationships
    roles = relationship("Role", secondary="role_permissions", back_populates="permissions")


class Role(Base, TimestampMixin):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(String(255), nullable=True)

    # Relationships
    permissions = relationship("Permission", secondary="role_permissions", back_populates="roles")
    users = relationship("User", secondary="user_roles", back_populates="roles")