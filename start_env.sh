#!/bin/bash
# FastAPI 后台服务框架 - 仅启动服务脚本 (后台运行)

set -e

echo "=== 启动 infra-demo 环境 ==="

echo "1. 启动 Docker 服务..."
docker-compose up -d

echo "2. 验证服务状态..."
sleep 2
docker-compose ps

echo ""
echo "=== 环境已就绪 ==="
echo "Docker: PostgreSQL(5433), Redis(6380)"
echo "执行 'poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000' 启动 FastAPI"
echo "执行 'poetry run celery -A app.celery_app worker --loglevel=info' 启动 Celery"
