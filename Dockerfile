FROM python:3.13-slim

WORKDIR /app

# Copy poetry files
COPY pyproject.toml poetry.lock* ./

# Use pip with faster options and no build isolation
# Use Aliyun mirror for faster downloads in China
RUN pip install --no-cache-dir --isolated -i https://mirrors.aliyun.com/pypi/simple/ fastapi "uvicorn[standard]" sqlalchemy asyncpg alembic redis celery pydantic-settings pydantic email-validator python-jose "passlib[bcrypt]" python-multipart bcrypt pytest pytest-asyncio httpx

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Default command - start FastAPI server
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]