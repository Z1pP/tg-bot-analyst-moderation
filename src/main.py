import asyncio
import logging
import sys

from bot import configure_dispatcher
from container import ContainerSetup
from scheduler import scheduler
from utils.logger_config import setup_logger

setup_logger(log_level=logging.INFO)

logger = logging.getLogger(__name__)


async def main():
    bot = None
    scheduler_instance = None
    try:
        logger.info("Инициализация контейнера...")
        ContainerSetup.setup()

        logger.info("Настройка и запуск бота...")
        bot, dp = await configure_dispatcher()

        # logger.info("Запускаем планировщик")
        # scheduler_instance = scheduler
        # schedule_daily_report(bot=bot)
        # scheduler_instance.start()
        # logger.info("Планировщик запущен успешно")

        logger.info("Бот запущен успешно. Начинаем polling...")
        await dp.start_polling(bot)

    except Exception as e:
        logger.error("Критическая ошибка: %s", str(e), exc_info=True)
        sys.exit(1)

    finally:
        logger.info("Завершение работы...")
        if scheduler_instance and scheduler_instance.running:
            scheduler_instance.shutdown()
            logger.info("Планировщик остановлен")

        if bot is not None and hasattr(bot, "session"):
            await bot.session.close()
            logger.info("Сессия бота закрыта")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Приложение остановлено пользователем")
        sys.exit(0)
