# Role Management API

Complete the RBAC system, add role CRUD API, role permission assignment, and user role assignment interfaces.

## New Files

| File | Description |
|------|-------------|
| `app/handler/entity/request/role.py` | RoleCreateRequest, RoleUpdateRequest, PermissionAssignRequest, UserRoleAssignRequest |
| `app/handler/entity/response/role.py` | RoleResponse, PermissionResponse, PaginatedRoleResponse, UserRoleResponse |
| `app/repository/role_repository.py` | RoleRepository (CRUD + relationship management) |
| `app/api/v1/endpoints/roles.py` | Role management API endpoints |

## Modified Files

| File | Description |
|------|-------------|
| `app/service/role_service.py` | Added create_role, get_role, list_roles_paginated, update_role, delete_role, assign_permissions, remove_permission, get_user_roles, assign_role_to_user, remove_role_from_user |
| `app/api/v1/router.py` | Register roles_router |

## API Endpoints

```
Role Management:
  GET    /api/v1/roles/              - List roles (paginated)
  POST   /api/v1/roles/              - Create role
  GET    /api/v1/roles/{role_id}      - Get role
  PUT    /api/v1/roles/{role_id}     - Update role
  DELETE /api/v1/roles/{role_id}     - Delete role

Role Permission Assignment:
  POST   /api/v1/roles/{role_id}/permissions              - Assign permissions
  DELETE /api/v1/roles/{role_id}/permissions/{perm_id}    - Remove permission

User Role Assignment:
  GET    /api/v1/roles/users/{user_id}/roles             - Get user roles
  POST   /api/v1/roles/users/{user_id}/roles             - Assign role
  DELETE /api/v1/roles/users/{user_id}/roles/{role_id}   - Remove role

User Permission Query:
  GET    /api/v1/users/{user_id}/permissions              - Get user all permissions (returns permission list directly)
```

## Permission Control

Use `require_permissions("roles:read")`, `require_permissions("roles:write")`, `require_permissions("roles:delete")`

## Verification

1. Rebuild container and test all endpoints
2. Use admin token to verify permission control
3. Run tests `docker-compose exec api python -m pytest tests/ -v`