import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logger(log_level: int = logging.INFO):
    """
    Настраивает глобальный логгер для всего приложения.
    Поддерживает вывод в консоль и в ротируемые файлы.

    :param log_level: Уровень логирования
    """

    # Формат сообщения
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(module)s.%(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Определяем имя сервиса для названия лог-файла
    service_name = os.getenv("SERVICE_NAME", "bot")

    # Путь к папке с логами
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / f"{service_name}.log"
    error_log_file = log_dir / f"{service_name}_error.log"

    # Обработчик для консоли
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Обработчик для общего файла с ротацией (10 MB, максимум 5 файлов)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)

    # Обработчик для ошибок с ротацией (10 MB, максимум 5 файлов)
    error_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)

    # Настройка корневого логгера
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Очищаем старые обработчики, если они были (чтобы избежать дублирования при повторном вызове)
    logger.handlers = []

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)

    logging.info(f"Logger configured successfully for service: {service_name}")
