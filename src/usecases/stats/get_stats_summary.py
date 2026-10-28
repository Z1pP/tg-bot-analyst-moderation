"""Use case: сводная статистика модерации для Mini App."""

from datetime import datetime

from dto.stats import StatsSummaryDTO
from repositories import PunishmentRepository, UserRepository
from services.time_service import TimeZoneService


class GetStatsSummaryUseCase:
    """Считает количество активных модераторов и действий модерации."""

    def __init__(
        self,
        punishment_repository: PunishmentRepository,
        user_repository: UserRepository,
    ) -> None:
        self._punishment_repository = punishment_repository
        self._user_repository = user_repository

    async def execute(self) -> StatsSummaryDTO:
        """Возвращает сводные метрики за сегодня и за всё время."""
        now = TimeZoneService.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

        moderators = await self._user_repository.get_all_moderators()
        today_actions = 0
        total_actions = 0
        for moderator in moderators:
            counts_today = await self._punishment_repository.get_punishment_counts_by_moderator(
                moderator_id=moderator.id,
                start_date=today_start,
                end_date=today_end,
            )
            counts_all = await self._punishment_repository.get_punishment_counts_by_moderator(
                moderator_id=moderator.id,
                start_date=datetime(2000, 1, 1),
                end_date=today_end,
            )
            today_actions += counts_today.get("warns", 0) + counts_today.get("bans", 0)
            total_actions += counts_all.get("warns", 0) + counts_all.get("bans", 0)

        return StatsSummaryDTO(
            active_users=len(moderators),
            moderation_actions=total_actions,
            today_actions=today_actions,
        )