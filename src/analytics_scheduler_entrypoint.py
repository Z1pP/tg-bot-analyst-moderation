import asyncio
import logging

from container import ContainerSetup, container
from repositories import UserRepository
from scheduler import broker
from services import BotMessageService
from tasks.analytics_tasks import (
    process_buffered_messages_task,
    process_buffered_reactions_task,
    process_buffered_replies_task,
)
from utils.exception_handler import notify_devs_about_error
from utils.logger_config import setup_logger

setup_logger(log_level=logging.INFO)
logger = logging.getLogger(__name__)

# Интервал проверки буферов (секунды)
ANALYTICS_CHECK_INTERVAL = 10


async def main():
    """Главная функция для запуска analytics scheduler"""
    ContainerSetup.setup()
    await broker.startup()
    logger.info(
        "Analytics Scheduler запущен (интервал: %d сек)", ANALYTICS_CHECK_INTERVAL
    )

    try:
        while True:
            try:
                # Запускаем задачи обработки буферов
                await (
                    process_buffered_messages_task.kicker()
                    .with_task_id("analytics:messages")
                    .kiq()
                )
                await (
                    process_buffered_reactions_task.kicker()
                    .with_task_id("analytics:reactions")
                    .kiq()
                )
                await (
                    process_buffered_replies_task.kicker()
                    .with_task_id("analytics:replies")
                    .kiq()
                )
            except Exception as e:
                logger.error(
                    "Ошибка при запуске задач обработки буферов: %s", e, exc_info=True
                )
                await notify_devs_about_error(
                    bot_message_service=container.resolve(BotMessageService),
                    user_repository=container.resolve(UserRepository),
                    exc=e,
                    context="analytics_scheduler_entrypoint: цикл запуска задач",
                )

            await asyncio.sleep(ANALYTICS_CHECK_INTERVAL)
    except asyncio.CancelledError:
        pass
    finally:
        await broker.shutdown()
        logger.info("Analytics Scheduler остановлен")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Приложение остановлено пользователем")
