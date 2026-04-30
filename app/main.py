from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine
from app.redis import redis_client
from app.api.router import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: verify connections
    async with engine.begin() as conn:
        # Optional: create tables if not using Alembic
        pass

    await redis_client.ping()

    yield

    # Shutdown: cleanup
    await engine.dispose()
    await redis_client.aclose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.APP_VERSION}
