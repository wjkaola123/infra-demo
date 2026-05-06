# Permission Module Design — CRUD Phase

## Context

Current RBAC system has permissions but no direct CRUD for them. Admins cannot create/update/delete permissions — only assign existing ones to roles. This phase adds permission maintenance capabilities.

| DELETE | `/api/v1/permissions/{id}` | Delete permission | `permissions:delete` |

## Schema

### CreatePermissionRequest
```python
name: str          # required, format: resource:action
description: str   # optional, max 255 chars
```

### UpdatePermissionRequest
```python
name: str          # optional
description: str   # optional
```

### PermissionResponse
```python
id: int
name: str
description: str | None
created_at: datetime
updated_at: datetime
```

## Name Validation Rules

- Required, non-empty
- Format: `resource:action` (one colon, exactly two parts)
- Characters: lowercase letters, numbers, underscores
- Max 50 chars total
- Unique in database (case-sensitive)

## Delete Behavior

- **409 Conflict** if permission is assigned to any role
- **404 Not Found** if permission doesn't exist

## Files to Create/Modify

### New Files
- `app/handler/entity/request/permission.py` — Create/Update request schemas
- `app/handler/entity/response/permission.py` — PermissionResponse schema
- `app/repository/permission_repository.py` — PermissionRepository (list, get, create, update, delete, check usage)
- `app/service/permission_service.py` — PermissionService (business logic)
- `app/api/v1/endpoints/permissions.py` — API endpoints

### Modified Files
- `app/api/v1/router.py` — Wire up `/permissions` prefix

## Required Permissions

| Permission | Used For |
|------------|----------|
| `permissions:read` | List, Get |
| `permissions:write` | Create, Update |
| `permissions:delete` | Delete |

## Implementation Order

1. Create request/response schemas
2. Create PermissionRepository (data access)
3. Create PermissionService (business logic)
4. Create permissions endpoint file
5. Wire up router
6. Add delete permission
7. Write migration for new permission seed data

## Verification

- Run `docker-compose exec api python -m pytest tests/ -v`
- Manual test with curl:
  - Create permission
  - List permissions
  - Get by ID
  - Update
  - Delete (should fail if in use)