# Plan: Permission 列表添加 assigned_roles_count 字段

## Context
在 Permission 列表页需要展示每个权限关联的角色数量，参考 Roles 列表中 `assigned_users_count` 的实现模式。

## 修改文件

### 1. Response DTO
**文件:** `app/handler/entity/response/permission.py`

在 `PermissionResponse` 中添加 `assigned_roles_count` 字段：
```python
class PermissionResponse(BaseModel):
    assigned_roles_count: int = 0  # 新增
```

### 2. Repository
**文件:** `app/repository/permission_repository.py`

修改 `list_paginated` 方法，参考 roles 的 `user_count_subquery` 模式，添加 `role_permissions` 表的计数子查询，返回 `(list[Permission], int, dict[int, int])` 三元组。

### 3. Service
**文件:** `app/service/permission_service.py`

修改 `list_permissions` 返回类型，传递 counts dict。

### 4. Endpoint
**文件:** `app/api/v1/endpoints/permissions.py`

在循环中设置 `assigned_roles_count`：
```python
for e in entities:
    response = PermissionResponse(...)
    response.assigned_roles_count = counts.get(e.id, 0)
    items.append(response)
```

## 验证
- 启动服务 `docker-compose up -d`
- 请求 `GET /api/v1/permissions/` 确认响应包含 `assigned_roles_count`
- 验证计数准确性（关联了角色的 permission 该值 > 0）

---

## 详细实现说明

### 核心思路
参考 Roles 列表中 `assigned_users_count` 的实现：通过 SQL 子查询统计关联表中的计数，使用 `outerjoin` 保证没有关联的记录也返回计数 0。

### 具体实现步骤

#### 1. Response DTO - 添加字段

**文件:** `app/handler/entity/response/permission.py`

```python
class PermissionResponse(BaseModel):
    id: int
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime | None
    assigned_roles_count: int = 0  # 新增
```

#### 2. Repository - 子查询计数

**文件:** `app/repository/permission_repository.py`

关键改动 `list_paginated` 方法，使用子查询统计每个 permission 关联的 role 数量：

```python
async def list_paginated(self, page: int, page_size: int, name: str | None = None) -> tuple[list[Permission], int, dict[int, int]]:
    offset = (page - 1) * page_size

    # 计数子查询：统计每个 permission 关联的 role 数量
    role_count_subquery = (
        select(
            role_permissions.c.permission_id,
            func.count(role_permissions.c.role_id).label('role_count')
        )
        .group_by(role_permissions.c.permission_id)
        .subquery()
    )

    # 基础查询：left outer join 计数子查询
    base_query = (
        select(Permission, func.coalesce(role_count_subquery.c.role_count, 0).label('assigned_roles_count'))
        .outerjoin(role_count_subquery, Permission.id == role_count_subquery.c.permission_id)
    )

    # 名称过滤
    if name:
        name_filter = Permission.name.ilike(f"%{name}%")
        base_query = base_query.where(name_filter)

    # 总数查询（不受分页影响）
    count_query = select(func.count(Permission.id))
    if name:
        count_query = count_query.where(name_filter)

    count_result = await self.session.execute(count_query)
    total = count_result.scalar() or 0

    # 分页查询
    result = await self.session.execute(
        base_query.order_by(Permission.id).offset(offset).limit(page_size)
    )

    # 组装返回结果
    permissions = []
    counts = {}
    for perm, count in result.all():
        permissions.append(perm)
        counts[perm.id] = count

    return permissions, total, counts
```

**SQL 等价于：**
```sql
SELECT p.*, COALESCE(rp_cnt.cnt, 0) as assigned_roles_count
FROM permissions p
LEFT OUTER JOIN (
    SELECT permission_id, COUNT(role_id) as cnt
    FROM role_permissions
    GROUP BY permission_id
) rp_cnt ON p.id = rp_cnt.permission_id
WHERE p.name ILIKE '%xxx%'  -- 条件可选
ORDER BY p.id
LIMIT page_size OFFSET offset
```

#### 3. Service - 透传 counts

**文件:** `app/service/permission_service.py`

```python
async def list_permissions(self, page: int, page_size: int, name: str | None) -> tuple[list[PermissionEntity], int, dict[int, int]]:
    items, total, counts = await self.repo.list_paginated(page, page_size, name)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    entities = [
        PermissionEntity(
            id=p.id,
            name=p.name,
            description=p.description,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )
        for p in items
    ]
    # 返回三元组：entities, total, {permission_id: count}
    return entities, total, {"page": page, "page_size": page_size, "total_pages": total_pages, "counts": counts}
```

#### 4. Endpoint - 设置到响应

**文件:** `app/api/v1/endpoints/permissions.py`

```python
@router.get("/", response_model=ApiResponse[PaginatedPermissionResponse])
async def list_permissions(...):
    service = PermissionService(db)
    entities, total, meta = await service.list_permissions(page, page_size, name)
    counts = meta.pop("counts")  # 取出计数 dict

    items = []
    for e in entities:
        resp = PermissionResponse(
            id=e.id,
            name=e.name,
            description=e.description,
            created_at=e.created_at,
            updated_at=e.updated_at,
            assigned_roles_count=counts.get(e.id, 0),  # 设置计数
        )
        items.append(resp)

    return ApiResponse(data=PaginatedPermissionResponse(
        items=items,
        total=total,
        page=meta["page"],
        page_size=meta["page_size"],
        total_pages=meta["total_pages"],
    ))
```

### 响应示例

```json
{
  "status": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "name": "users:read",
        "description": "读取用户",
        "created_at": "2026-01-01T00:00:00",
        "updated_at": null,
        "assigned_roles_count": 3
      },
      {
        "id": 2,
        "name": "users:write",
        "description": "写入用户",
        "created_at": "2026-01-01T00:00:00",
        "updated_at": null,
        "assigned_roles_count": 0
      }
    ],
    "total": 2,
    "page": 1,
    "page_size": 20,
    "total_pages": 1
  }
}
```

---

## 测试用例修改计划

### 1. API 测试 - 修改 `test_list_permissions`

**文件:** `tests/test_api/test_permissions.py` (第 120-141 行)

修改现有测试，验证 `assigned_roles_count` 字段存在：

```python
@pytest.mark.asyncio
async def test_list_permissions(client: AsyncClient, db_session):
    """Test listing permissions with pagination."""
    token = await get_admin_token(client, db_session, "listperm")

    response = await client.get(
        "/api/v1/permissions/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "success"
    assert "items" in data["data"]
    assert "total" in data["data"]
    assert "page" in data["data"]
    assert "page_size" in data["data"]
    assert "total_pages" in data["data"]
    assert isinstance(data["data"]["items"], list)
    for perm in data["data"]["items"]:
        assert "id" in perm
        assert "name" in perm
        assert "description" in perm
        assert "assigned_roles_count" in perm  # 新增
        assert isinstance(perm["assigned_roles_count"], int)  # 新增
        assert perm["assigned_roles_count"] >= 0  # 新增
```

### 2. API 测试 - 新增 `test_list_permissions_returns_assigned_roles_count`

**文件:** `tests/test_api/test_permissions.py`

新增测试验证计数准确性（参考 `test_roles.py` 中 `test_list_roles` 的 `assigned_users_count` 验证模式）：

```python
@pytest.mark.asyncio
async def test_list_permissions_returns_assigned_roles_count(client: AsyncClient, db_session):
    """Test that list permissions returns correct assigned_roles_count."""
    from sqlalchemy import text

    token = await get_admin_token(client, db_session, "countrolesperm")
    timestamp = int(time.time() * 1000)

    # 1. 创建一个新 permission（初始无角色关联，count 应为 0）
    create_response = await client.post(
        "/api/v1/permissions/",
        json={"name": f"count_test_{timestamp}", "description": "Test count"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert create_response.status_code == 201
    perm_id = create_response.json()["data"]["id"]

    # 2. 列出 permissions，验证新创建的 permission 的 assigned_roles_count 为 0
    list_response = await client.get(
        "/api/v1/permissions/",
        headers={"Authorization": f"Bearer {token}"}
    )
    items = list_response.json()["data"]["items"]
    new_perm = next(p for p in items if p["id"] == perm_id)
    assert new_perm["assigned_roles_count"] == 0

    # 3. 获取 admin role id（role_id = 1）
    result = await db_session.execute(text("SELECT id FROM roles WHERE name = 'admin'"))
    admin_role_id = result.scalar_one()

    # 4. 将新 permission 分配给 admin role
    await db_session.execute(
        text("INSERT INTO role_permissions (role_id, permission_id) VALUES (:role_id, :perm_id)"),
        {"role_id": admin_role_id, "perm_id": perm_id}
    )
    await db_session.commit()

    # 5. 再次列出 permissions，验证 assigned_roles_count 为 1
    list_response = await client.get(
        "/api/v1/permissions/",
        headers={"Authorization": f"Bearer {token}"}
    )
    items = list_response.json()["data"]["items"]
    new_perm = next(p for p in items if p["id"] == perm_id)
    assert new_perm["assigned_roles_count"] == 1

    # 6. 再分配给一个 role（分配给 editor role）
    result = await db_session.execute(text("SELECT id FROM roles WHERE name = 'editor'"))
    editor_role_id = result.scalar_one()
    await db_session.execute(
        text("INSERT INTO role_permissions (role_id, permission_id) VALUES (:role_id, :perm_id)"),
        {"role_id": editor_role_id, "perm_id": perm_id}
    )
    await db_session.commit()

    # 7. 验证 assigned_roles_count 为 2
    list_response = await client.get(
        "/api/v1/permissions/",
        headers={"Authorization": f"Bearer {token}"}
    )
    items = list_response.json()["data"]["items"]
    new_perm = next(p for p in items if p["id"] == perm_id)
    assert new_perm["assigned_roles_count"] == 2

    # 8. 清理
    await db_session.execute(
        text("DELETE FROM role_permissions WHERE permission_id = :perm_id"),
        {"perm_id": perm_id}
    )
    await db_session.commit()
```

### 3. Repository 测试 - 新增 `test_list_paginated_returns_assigned_roles_count`

**文件:** `tests/repository/test_permission_repository.py`（如果不存在则创建）

参考 `test_role_repository.py` 中的 `test_list_paginated_returns_assigned_users_count`：

```python
@pytest.mark.asyncio
async def test_list_paginated_returns_assigned_roles_count(db_session):
    """Test that list_paginated returns assigned_roles_count correctly."""
    from app.repository.permission_repository import PermissionRepository
    from app.repository.entity.role import Role

    repository = PermissionRepository(db_session)

    # 创建两个 test permissions
    perm1 = await repository.create(name=f"perm1_{int(time.time() * 1000)}", description="Perm 1")
    perm2 = await repository.create(name=f"perm2_{int(time.time() * 1000)}", description="Perm 2")

    # 初始状态：所有 permission 的 assigned_roles_count 都为 0
    permissions, total, counts = await repository.list_paginated(1, 99999)
    assert counts.get(perm1.id, 0) == 0
    assert counts.get(perm2.id, 0) == 0

    # 创建一个 role 并将 perm1 分配给它
    role = Role(name=f"test_role_{int(time.time() * 1000)}", description="Test role")
    db_session.add(role)
    await db_session.commit()
    await db_session.refresh(role)

    from app.repository.role_repository import RoleRepository
    role_repo = RoleRepository(db_session)
    await role_repo.assign_permission_to_role(role_id=role.id, permission_id=perm1.id)

    # 验证 perm1 的 assigned_roles_count 为 1，perm2 为 0
    permissions, total, counts = await repository.list_paginated(1, 99999)
    assert counts.get(perm1.id, 0) == 1
    assert counts.get(perm2.id, 0) == 0

    # 再将 perm1 分配给另一个 role
    role2 = Role(name=f"test_role2_{int(time.time() * 1000)}", description="Test role 2")
    db_session.add(role2)
    await db_session.commit()
    await db_session.refresh(role2)
    await role_repo.assign_permission_to_role(role_id=role2.id, permission_id=perm1.id)

    # 验证 perm1 的 assigned_roles_count 为 2
    permissions, total, counts = await repository.list_paginated(1, 99999)
    assert counts.get(perm1.id, 0) == 2

    # 清理
    await role_repo.remove_permission_from_role(role_id=role.id, permission_id=perm1.id)
    await role_repo.remove_permission_from_role(role_id=role2.id, permission_id=perm1.id)
    await repository.delete(perm1.id)
    await repository.delete(perm2.id)
    await db_session.delete(role)
    await db_session.delete(role2)
    await db_session.commit()
```

### 4. 修改汇总

| 文件 | 修改类型 | 说明 |
|------|---------|------|
| `tests/test_api/test_permissions.py` | 修改 | `test_list_permissions` 新增 `assigned_roles_count` 字段断言 |
| `tests/test_api/test_permissions.py` | 新增 | `test_list_permissions_returns_assigned_roles_count` 测试计数准确性 |
| `tests/repository/test_permission_repository.py` | 新增 | `test_list_paginated_returns_assigned_roles_count` repository 层测试 |

## 未解决问题
无
