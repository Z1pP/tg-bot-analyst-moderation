import logging
import sys


def setup_logger(log_level: int = logging.INFO):
    """
    Настраивает глобальный логгер для всего приложения (только в консоль).

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

    # Настройка корневого логгера
    logger = logging.getLogger()
    logger.setLevel(log_level)
    logger.addHandler(console_handler)

    logging.info("Logger configured successfully (console only).")
