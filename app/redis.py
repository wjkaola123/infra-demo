from redis.asyncio import Redis, from_url

from app.config import settings


redis_client: Redis = from_url(settings.REDIS_URL, decode_responses=True)
