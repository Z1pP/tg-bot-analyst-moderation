import asyncio
import logging
import os
import sys
from pathlib import Path

from bot import init_bot
from utils.logger_config import setup_logger

# Создание папки для хранения логов
BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_FOLDER = BASE_DIR / "logs"
os.makedirs(LOGS_FOLDER, exist_ok=True)

setup_logger(log_file=LOGS_FOLDER / "bot.log", log_level=logging.DEBUG)

logger = logging.getLogger(__name__)


async def main():
    try:
        logger.info("Старт бота...")
        bot, dp = await init_bot()
        logger.info("Бот запущен успешно.")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error("Непредвиденная ошибка: %s", str(e), exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Закрывает сессию...")
        await bot.session.close()
        logger.info("Сессия закрыта успешно.")


if __name__ == "__main__":
    asyncio.run(main())
