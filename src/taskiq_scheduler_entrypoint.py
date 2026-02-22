import asyncio
import logging

from container import ContainerSetup, container
from repositories import UserRepository
from scheduler import broker
from services import BotMessageService
from services.scheduler import TaskiqSchedulerService
from utils.exception_handler import notify_devs_about_error
from utils.logger_config import setup_logger

setup_logger(log_level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    ContainerSetup.setup()
    await broker.startup()
    logger.info("TaskIQ scheduler запущен")

    taskiq_service: TaskiqSchedulerService = container.resolve(TaskiqSchedulerService)

    try:
        while True:
            try:
                await taskiq_service.tick()
            except Exception as e:
                logger.error("Ошибка в тике scheduler: %s", e, exc_info=True)
                await notify_devs_about_error(
                    bot_message_service=container.resolve(BotMessageService),
                    user_repository=container.resolve(UserRepository),
                    exc=e,
                    context="taskiq_scheduler_entrypoint: tick()",
                )

            await asyncio.sleep(60)
    except asyncio.CancelledError:
        pass
    finally:
        await broker.shutdown()
        logger.info("Scheduler остановлен")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Приложение остановлено пользователем")
