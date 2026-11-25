from redis import Redis
from redis.exceptions import RedisError

from app.core.config import settings

redis_client = Redis.from_url(settings.redis_url, socket_connect_timeout=2, socket_timeout=2)


def check_redis() -> bool:
    try:
        return bool(redis_client.ping())
    except RedisError:
        return False
