#!/bin/bash
# FastAPI 后台服务框架 - 快速启动脚本

set -e

echo "=== 1. 启动 Docker 服务 (PostgreSQL + Redis) ==="
docker-compose up -d

echo ""
echo "=== 2. 安装 Poetry 依赖 ==="
poetry install

echo ""
echo "=== 3. 应用数据库迁移 ==="
poetry run alembic upgrade head

echo ""
echo "=== 4. 启动 FastAPI ==="
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
FASTAPI_PID=$!

echo ""
echo "=== 5. 启动 Celery Worker ==="
poetry run celery -A app.celery_app worker --loglevel=info &
CELERY_PID=$!

echo ""
echo "=== 服务已启动 ==="
echo "FastAPI: http://localhost:8000 (PID: $FASTAPI_PID)"
echo "Swagger UI: http://localhost:8000/docs"
echo "Celery Worker: (PID: $CELERY_PID)"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待信号
trap "echo '正在停止服务...'; kill $FASTAPI_PID $CELERY_PID 2>/dev/null; docker-compose down; exit 0" INT TERM

wait
