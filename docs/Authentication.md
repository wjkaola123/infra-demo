# Authentication Module

**Goal:** Implement user registration, login, and JWT token issuance.

## Context

User chose **full permission system** + **password field** authentication. Authentication module is the first step, mainly implementing user authentication and JWT token issuance.

## Technical Solution

### Database Model

```
users (existing, extended)
├── id, username, email (existing)
├── password_hash (new)
├── is_active (existing)
└── created_at, updated_at (existing)
```

## Implementation Steps

### Step 1.1: Add Dependencies

**pyproject.toml additions:**
```toml
python-jose = "^3.3.0"
passlib = {extras = ["bcrypt"]}
python-multipart = "^0.0.9"
```

### Step 1.2: Extend User Model

**app/repository/entity/user.py:**
- Add `password_hash` field

### Step 1.3: Create Auth Service

**app/tools/auth/hashing.py:**
- Password hashing/verification (bcrypt)

**app/tools/auth/jwt.py:**
- `JWTHandler` class - create/verify tokens
- `create_access_token()`
- `create_refresh_token()`
- `decode_token()`
- `verify_token()`

**app/service/auth_service.py:**
- `AuthService` class - encapsulate register/login/refresh token business logic

### Step 1.4: Create Auth API

**app/api/v1/endpoints/auth.py:**
```
POST /api/v1/auth/register   - Register user
POST /api/v1/auth/login      - Login to get JWT
POST /api/v1/auth/refresh    - Refresh token
```

### Step 1.5: Create Alembic Migration

```
002_add_password_hash_to_users.py
```

## Key Files

| File | Purpose |
|------|---------|
| `app/repository/entity/user.py` | User model (new password_hash) |
| `app/tools/auth/hashing.py` | Password encryption/verification |
| `app/tools/auth/jwt.py` | JWT utility class |
| `app/service/auth_service.py` | Auth business logic |
| `app/api/v1/endpoints/auth.py` | Auth API (register/login/refresh) |

## Verification Plan

```bash
# 1. Start services
docker-compose up -d --build

# 2. Run migrations
poetry run alembic upgrade head

# 3. Test registration
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","email":"admin@test.com","password":"admin123"}'

# 4. Test login to get token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=admin&password=admin123"

# 5. Test token refresh
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Authorization: Bearer <refresh_token>"
```