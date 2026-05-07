from sqlalchemy import Column, Integer, String, Table, ForeignKey, event
from sqlalchemy.orm import relationship
from app.repository.entity.base import Base, TimestampMixin
from app.service.activity_log_service import (
    receive_after_insert,
    receive_before_update,
    receive_after_update,
    receive_before_delete,
)


# Association table: user-role
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)

# Association table: role-permission
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)


class Permission(Base, TimestampMixin):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(String(255), nullable=True)


class Role(Base, TimestampMixin):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(String(255), nullable=True)

    permissions = relationship(
        "Permission",
        secondary=role_permissions,
        lazy="selectin",
    )


event.listens_for(Role, "after_insert")(receive_after_insert)
event.listens_for(Role, "before_update")(receive_before_update)
event.listens_for(Role, "after_update")(receive_after_update)
event.listens_for(Role, "before_delete")(receive_before_delete)

event.listens_for(Permission, "after_insert")(receive_after_insert)
event.listens_for(Permission, "before_update")(receive_before_update)
event.listens_for(Permission, "after_update")(receive_after_update)
event.listens_for(Permission, "before_delete")(receive_before_delete)
