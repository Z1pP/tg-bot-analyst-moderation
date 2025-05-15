from datetime import datetime, time, timedelta, timezone

from dto.activity import CreateActivityDTO, ResultActivityDTO
from dto.message import ResultMessageDTO
from models import ModeratorActivity
from repositories import ActivityRepository


class TrackModeratorActivityUseCase:
    def __init__(self, activivty_repository: ActivityRepository):
        self.activity_repository = activivty_repository
        super().__init__()

    async def execute(self, message_dto: ResultMessageDTO) -> ResultActivityDTO:
        """
        Трекает все сообщения которые не являются reply на другие сообщения
        """
        last_activity = await self.activity_repository.get_last_activity(
            user_id=message_dto.db_user_id, chat_id=message_dto.db_chat_id
        )

        if last_activity:
            activity_dto = CreateActivityDTO(
                user_id=message_dto.db_user_id,
                chat_id=message_dto.db_chat_id,
                last_message_id=last_activity.next_message_id,
                next_message_id=message_dto.id,
                inactive_period_seconds=self._calcutale_inactive_period(
                    last_activity=last_activity
                ),
            )
            new_activity = await self.activity_repository.create_activity(
                dto=activity_dto
            )
            return ResultActivityDTO.from_model(new_activity)
        else:
            # Если активности нет, то создаем новую
            activity_dto = CreateActivityDTO(
                user_id=message_dto.db_user_id,
                chat_id=message_dto.db_chat_id,
                last_message_id=message_dto.id,
                next_message_id=message_dto.id,
                inactive_period_seconds=0,
            )
            new_activity = await self.activity_repository.create_activity(
                dto=activity_dto
            )
            return ResultActivityDTO.from_model(model=new_activity)

    def _calcutale_inactive_period(self, last_activity: ModeratorActivity) -> int:
        """
        Вычисляет период неактивности с учётом рабочего времени.
        """
        created_date = last_activity.created_at
        if created_date.tzinfo is None:
            created_date = created_date.replace(tzinfo=timezone.utc)

        current_date = datetime.now(timezone.utc)

        # Рабочее время модераторов
        work_start = time(10, 0)  # 10:00
        work_end = time(22, 0)  # 22:00
        tolerance = timedelta(minutes=10)  # Допустимое отклонение

        # Проверяем, попадает ли текущее время в рабочий интервал
        if not self._is_within_working_hours(
            current_date.time(), work_start, work_end, tolerance
        ):
            return 0  # Если сообщение вне рабочего времени, период неактивности не увеличивается

        # Рассчитываем период неактивности
        inactive_period = current_date - created_date
        return inactive_period.total_seconds()

    def _is_within_working_hours(
        self, current_time: time, start: time, end: time, tolerance: timedelta
    ) -> bool:
        """
        Проверяет, попадает ли текущее время в рабочий интервал с учётом допустимого отклонения.
        """
        start_with_tolerance = (
            datetime.combine(datetime.today(), start) - tolerance
        ).time()
        end_with_tolerance = (
            datetime.combine(datetime.today(), end) + tolerance
        ).time()

        if start_with_tolerance <= current_time <= end_with_tolerance:
            return True
        return False
