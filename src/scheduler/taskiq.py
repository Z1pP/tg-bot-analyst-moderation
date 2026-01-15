import logging

from taskiq_redis import RedisAsyncResultBackend, RedisStreamBroker

from config import settings
from utils.logger_config import setup_logger

# Инициализируем логгер для воркера
setup_logger(log_level=logging.INFO)

result_backend = RedisAsyncResultBackend(
    redis_url=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
)

broker = RedisStreamBroker(
    url=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
).with_result_backend(result_backend)
