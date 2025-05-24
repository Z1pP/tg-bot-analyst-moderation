from datetime import datetime, time, timedelta, timezone
from typing import Optional

from constants.work_time import TOLERANCE, WORK_END, WORK_START
from dto.activity import CreateActivityDTO, ResultActivityDTO
from dto.message import ResultMessageDTO
from models import ModeratorActivity
from repositories import ActivityRepository
from services.time_service import TimeZoneService


class TrackModeratorActivityUseCase:
    def __init__(self, activity_repository: ActivityRepository):
        self.activity_repository = activity_repository

    async def execute(self, message_dto: ResultMessageDTO) -> ResultActivityDTO:
        """
        Трекает активность модератора на основе отправленных сообщений.

        Args:
            message_dto: DTO с информацией о сообщении

        Returns:
            DTO с результатом трекинга активности
        """
        last_activity = await self._get_last_activity(message_dto)

        if last_activity:
            inactive_seconds = self._calculate_inactive_period(last_activity)
            activity_dto = self._build_activity_dto(
                message_dto, last_activity.next_message_id, inactive_seconds
            )
        else:
            activity_dto = self._build_activity_dto(message_dto, message_dto.id, 0)

        new_activity = await self.activity_repository.create_activity(activity_dto)
        return ResultActivityDTO.from_model(new_activity)

    async def _get_last_activity(
        self, message_dto: ResultMessageDTO
    ) -> Optional[ModeratorActivity]:
        """Получает последнюю активность модератора в чате."""
        return await self.activity_repository.get_last_activity(
            user_id=message_dto.db_user_id, chat_id=message_dto.db_chat_id
        )

    def _build_activity_dto(
        self, message_dto: ResultMessageDTO, last_message_id: int, inactive_seconds: int
    ) -> CreateActivityDTO:
        """Создает DTO для новой активности."""
        return CreateActivityDTO(
            user_id=message_dto.db_user_id,
            chat_id=message_dto.db_chat_id,
            last_message_id=last_message_id,
            next_message_id=message_dto.id,
            inactive_period_seconds=inactive_seconds,
        )

    def _calculate_inactive_period(self, last_activity: ModeratorActivity) -> int:
        """
        Вычисляет период неактивности с учетом рабочего времени.

        Args:
            last_activity: Последняя зарегистрированная активность

        Returns:
            Количество секунд неактивности (0 если вне рабочего времени)
        """
        created_date = self._ensure_timezone(last_activity.created_at)
        current_date = TimeZoneService.now()

        # Не считаем период если разные даты или вне рабочего времени
        if created_date.date() != current_date.date() or not self._is_working_time(
            current_date
        ):
            return 0

        return int((current_date - created_date).total_seconds())

    def _ensure_timezone(self, dt: datetime) -> datetime:
        """Добавляет временную зону если отсутствует."""
        if dt is None:
            return TimeZoneService.now()
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

    def _is_working_time(self, current_dt: datetime) -> bool:
        """
        Проверяет, попадает ли текущее время в рабочий интервал.

        Args:
            current_dt: Текущее время с временной зоной

        Returns:
            True если рабочее время, иначе False
        """
        current_time = current_dt.time()
        start = self._adjust_time_with_tolerance(WORK_START, -TOLERANCE)
        end = self._adjust_time_with_tolerance(WORK_END, TOLERANCE)

        return start <= current_time <= end

    def _adjust_time_with_tolerance(self, base_time: time, delta: timedelta) -> time:
        """Корректирует время с учетом допуска."""
        adjusted = datetime.combine(datetime.today(), base_time) + delta
        return adjusted.time()
