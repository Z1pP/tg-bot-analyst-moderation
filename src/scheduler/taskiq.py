import logging

from taskiq_redis import RedisAsyncResultBackend, RedisStreamBroker

from config import settings
from utils.logger_config import setup_logger

# Инициализируем логгер для воркера
setup_logger(log_level=logging.INFO)

result_backend = RedisAsyncResultBackend(
    redis_url=settings.REDIS_URL,
)

broker = RedisStreamBroker(
    url=settings.REDIS_URL,
).with_result_backend(result_backend)
