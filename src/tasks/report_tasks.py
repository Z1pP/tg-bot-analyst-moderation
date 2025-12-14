import logging

from constants.period import TimePeriod
from container import ContainerSetup, container
from scheduler import broker
from services.report_schedule_service import ReportScheduleService
from usecases.report.chat.send_daily_chat_reports import SendDailyChatReportsUseCase

logger = logging.getLogger(__name__)

ContainerSetup.setup()


@broker.task
async def send_chat_report_task(
    schedule_id: int,
    user_id: int,
    chat_id: int,
    period: str = TimePeriod.TODAY.value,
):
    """
    Задача для отправки ежедневного отчета по расписанию.

    Args:
        schedule_id: ID расписания (для логирования)
        user_id: ID пользователя (админа)
        chat_id: ID чата
        period: Период для отчета
    """
    logger.info(
        "Выполнение задачи отправки отчета: schedule_id=%s, user_id=%s, chat_id=%s, period=%s",
        schedule_id,
        user_id,
        chat_id,
        period,
    )

    try:
        schedule_service: ReportScheduleService = container.resolve(
            ReportScheduleService
        )
        schedule = await schedule_service.get_schedule(user_id=user_id, chat_id=chat_id)

        if not schedule:
            logger.warning(
                "Расписание не найдено для schedule_id=%s, user_id=%s, chat_id=%s. Пропускаем выполнение.",
                schedule_id,
                user_id,
                chat_id,
            )
            return
    except Exception as e:
        logger.error(
            "Ошибка при получении расписания schedule_id=%s: %s",
            schedule_id,
            e,
            exc_info=True,
        )
        raise

    if not schedule.enabled:
        logger.info(
            "Рассылка отключена для schedule_id=%s, user_id=%s, chat_id=%s. Пропускаем выполнение.",
            schedule_id,
            user_id,
            chat_id,
        )
        return

    try:
        usecase: SendDailyChatReportsUseCase = container.resolve(
            SendDailyChatReportsUseCase
        )
        await usecase.execute(user_id=user_id, chat_id=chat_id, period=period)
        logger.info(
            "Задача отправки отчета выполнена успешно: schedule_id=%s", schedule_id
        )
    except Exception as e:
        logger.error(
            "Ошибка при выполнении задачи отправки отчета schedule_id=%s: %s",
            schedule_id,
            e,
            exc_info=True,
        )
        raise
