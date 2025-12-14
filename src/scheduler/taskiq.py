from taskiq_redis import RedisAsyncResultBackend, RedisStreamBroker

from config import settings

result_backend = RedisAsyncResultBackend(
    redis_url=settings.REDIS_URL,
)

broker = RedisStreamBroker(
    url=settings.REDIS_URL,
).with_result_backend(result_backend)
