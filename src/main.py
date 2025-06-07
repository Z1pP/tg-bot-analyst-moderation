import asyncio
import logging
import sys

from bot import init_bot
from utils.logger_config import setup_logger

setup_logger(log_level=logging.DEBUG)

logger = logging.getLogger(__name__)


async def main():
    bot = None
    try:
        logger.info("Старт бота...")
        bot, dp = await init_bot()
        logger.info("Бот запущен успешно.")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error("Непредвиденная ошибка: %s", str(e), exc_info=True)
        sys.exit(1)
    finally:
        if bot is not None and hasattr(bot, "session"):
            logger.info("Закрывает сессию...")
            await bot.session.close()
            logger.info("Сессия закрыта успешно.")


if __name__ == "__main__":
    asyncio.run(main())
