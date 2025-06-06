from redis.client import Redis

from src.settings import settings

redis = Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    username=settings.redis_username,
    password=settings.redis_password,
    decode_responses=True,
)
