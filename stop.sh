#!/bin/bash
# FastAPI 后台服务框架 - 停止脚本

echo "=== 停止所有服务 ==="

# 停止 uvicorn 和 celery
pkill -f "uvicorn app.main:app" 2>/dev/null || true
pkill -f "celery.*celery_app" 2>/dev/null || true

# 停止 Docker 服务
echo "停止 Docker 服务..."
docker-compose down 2>/dev/null || true

echo "所有服务已停止"
