from sqlalchemy.orm import Mapper
from sqlalchemy.engine import Connection
from app.context import audit_context


def _resource_type_for_model(model_tablename: str) -> str:
    mapping = {
        "users": "user",
        "roles": "role",
        "permissions": "permission",
    }
    return mapping.get(model_tablename, model_tablename)


def _model_to_dict(model) -> dict:
    result = {}
    for column in model.__table__.columns:
        value = getattr(model, column.name)
        if hasattr(value, "to_dict"):
            result[column.name] = value.to_dict()
        elif hasattr(value, "__dict__"):
            pass
        else:
            result[column.name] = value
    return result


def _write_activity_log(
    connection: Connection,
    action: str,
    target,
    old_value: dict | None,
    new_value: dict | None,
) -> None:
    ctx = audit_context.get()
    if not ctx:
        return
    resource_type = _resource_type_for_model(target.__table__.name)
    resource_id = target.id
    # Use raw SQL insert since we're in SQLAlchemy event context (outside async session)
    from sqlalchemy import insert
    from app.repository.entity.activity_log import ActivityLog
    connection.execute(
        insert(ActivityLog).values(
            actor_user_id=ctx.user_id,
            actor_username=ctx.username,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_value=old_value,
            new_value=new_value,
            ip_address=ctx.ip_address,
        )
    )


def receive_after_insert(mapper: Mapper, connection: Connection, target) -> None:
    _write_activity_log(connection, "CREATE", target, None, _model_to_dict(target))


def receive_before_update(mapper: Mapper, connection: Connection, target) -> None:
    target._audit_old_values = {c.name: getattr(target, c.name) for c in target.__table__.columns}


def receive_after_update(mapper: Mapper, connection: Connection, target) -> None:
    if not hasattr(target, "_audit_old_values"):
        return
    old_value = target._audit_old_values
    new_value = _model_to_dict(target)
    _write_activity_log(connection, "UPDATE", target, old_value, new_value)
    del target._audit_old_values


def receive_before_delete(mapper: Mapper, connection: Connection, target) -> None:
    _write_activity_log(connection, "DELETE", target, _model_to_dict(target), None)