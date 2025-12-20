import logging

from constants.period import TimePeriod
from repositories import ReportScheduleRepository

logger = logging.getLogger(__name__)


class TaskiqSchedulerService:
    def __init__(self, schedule_repo: ReportScheduleRepository) -> None:
        self._schedule_repo = schedule_repo

    async def tick(self):
        logger.debug("Идем в бд за задачами")
        due_schedules = await self._schedule_repo.get_due_schedules_and_reschedule()

        if due_schedules:
            logger.info(f"Отправляем {len(due_schedules)} задач в очередь")

        from tasks.report_tasks import send_chat_report_task

        for schedule in due_schedules:
            unique_task_id = f"{schedule.id}:{schedule.last_run_at.isoformat()}"

            await (
                send_chat_report_task.kicker()
                .with_task_id(unique_task_id)
                .kiq(
                    schedule_id=schedule.id,
                    chat_id=schedule.chat_id,
                    period=TimePeriod.TODAY.value,
                )
            )
