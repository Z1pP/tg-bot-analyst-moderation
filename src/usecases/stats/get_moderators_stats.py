"""Use case: разбивка наказаний по модераторам для Mini App."""

from datetime import datetime

from dto.stats import ModeratorStatsDTO, ModeratorsStatsDTO
from repositories import PunishmentRepository, UserRepository


class GetModeratorsStatsUseCase:
    """Считает варны и баны каждого модератора за период."""

    def __init__(
        self,
        punishment_repository: PunishmentRepository,
        user_repository: UserRepository,
    ) -> None:
        self._punishment_repository = punishment_repository
        self._user_repository = user_repository

    async def execute(
        self,
        period: str,
        start_date: datetime,
        end_date: datetime,
    ) -> ModeratorsStatsDTO:
        """Возвращает разбивку наказаний по модераторам, отсортированную по total."""
        moderators = await self._user_repository.get_all_moderators()
        if not moderators:
            return ModeratorsStatsDTO(moderators=[], period=period)

        moderator_ids = [moderator.id for moderator in moderators]
        counts_by_id = (
            await self._punishment_repository.get_punishment_counts_by_moderators(
                moderator_ids=moderator_ids,
                start_date=start_date,
                end_date=end_date,
            )
        )

        result = []
        for moderator in moderators:
            counts = counts_by_id.get(moderator.id, {"warns": 0, "bans": 0})
            warns = counts["warns"]
            bans = counts["bans"]
            result.append(
                ModeratorStatsDTO(
                    username=moderator.username or f"ID:{moderator.tg_id}",
                    tg_id=moderator.tg_id,
                    warns=warns,
                    bans=bans,
                    total=warns + bans,
                )
            )

        result.sort(key=lambda item: item.total, reverse=True)
        return ModeratorsStatsDTO(moderators=result, period=period)