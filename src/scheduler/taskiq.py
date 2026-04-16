import logging

from taskiq_aio_pika import AioPikaBroker, Queue
from taskiq_redis import RedisAsyncResultBackend

from config import settings
from utils.logger_config import setup_logger

# Инициализируем логгер для воркера
setup_logger(log_level=logging.INFO)

result_backend = RedisAsyncResultBackend(
    redis_url=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
)

broker = AioPikaBroker(
    url=f"amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PASS}@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}/",
    delay_queue=Queue(name="taskiq.delay_queue"),
).with_result_backend(result_backend)
