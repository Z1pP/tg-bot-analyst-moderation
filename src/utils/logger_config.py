import logging
import sys
from logging.handlers import RotatingFileHandler


def setup_logger(log_file: str = "bot.log", log_level: int = logging.INFO):
    """
    Настраивает глобальный логгер для всего приложения.

    :param log_file: Путь к файлу логов
    :param log_level: Уровень логирования
    """

    # Формат сообщения
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(module)s.%(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Обработчик для консоли
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Обработчик для файла (с ротацией)
    file_handler = RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    # Настройка корневого логгера
    logger = logging.getLogger()
    logger.setLevel(log_level)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    logging.info("Logger configured successfully.")
