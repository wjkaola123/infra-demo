# Role Management API

完善 RBAC 体系，新增角色 CRUD API、角色权限分配、用户角色分配接口。

## 新增文件

| 文件 | 说明 |
|------|------|
| `app/handler/entity/request/role.py` | RoleCreateRequest, RoleUpdateRequest, PermissionAssignRequest, UserRoleAssignRequest |
| `app/handler/entity/response/role.py` | RoleResponse, PermissionResponse, PaginatedRoleResponse, UserRoleResponse |
| `app/repository/role_repository.py` | RoleRepository (CRUD + 关系管理) |
| `app/api/v1/endpoints/roles.py` | 角色管理 API 端点 |

## 修改文件

| 文件 | 说明 |
|------|------|
| `app/service/role_service.py` | 新增 create_role, get_role, list_roles_paginated, update_role, delete_role, assign_permissions, remove_permission, get_user_roles, assign_role_to_user, remove_role_from_user |
| `app/api/v1/router.py` | 注册 roles_router |

## API 端点

```
角色管理:
  GET    /api/v1/roles/              - 角色列表（分页）
  POST   /api/v1/roles/              - 创建角色
  GET    /api/v1/roles/{role_id}      - 获取角色
  PUT    /api/v1/roles/{role_id}     - 更新角色
  DELETE /api/v1/roles/{role_id}     - 删除角色

角色权限分配:
  POST   /api/v1/roles/{role_id}/permissions              - 分配权限
  DELETE /api/v1/roles/{role_id}/permissions/{perm_id}    - 移除权限

用户角色分配:
  GET    /api/v1/roles/users/{user_id}/roles             - 获取用户角色
  POST   /api/v1/roles/users/{user_id}/roles             - 分配角色
  DELETE /api/v1/roles/users/{user_id}/roles/{role_id}   - 移除角色

用户权限查询:
  GET    /api/v1/users/{user_id}/permissions              - 获取用户所有权限（直接返回权限列表）
```

## 权限控制

使用 `require_permissions("roles:read")`, `require_permissions("roles:write")`, `require_permissions("roles:delete")`

## 验证

1. API 重建容器后测试各端点
2. 使用 admin token 调用验证权限控制
3. 运行测试 `docker-compose exec api python -m pytest tests/ -v`
