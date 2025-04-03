import redis.asyncio as redis
from .secrets import CACHE_URL


pool = redis.ConnectionPool.from_url(CACHE_URL, decode_responses=True)


def get_redis():
    return redis.Redis(connection_pool=pool)
