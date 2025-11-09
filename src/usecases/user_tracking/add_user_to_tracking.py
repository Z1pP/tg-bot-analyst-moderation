import logging
from dataclasses import dataclass
from typing import Optional

from dto import UserTrackingDTO
from repositories import UserTrackingRepository
from services import UserService
from constants import Dialog

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AddUserToTrackingResult:
    success: bool
    message: Optional[str] = None


class AddUserToTrackingUseCase:
    def __init__(
        self,
        user_service: UserService,
        user_tracking_repository: UserTrackingRepository,
    ):
        self._user_tracking_repository = user_tracking_repository
        self._user_service = user_service

    async def execute(self, dto: UserTrackingDTO) -> AddUserToTrackingResult:
        user = await self._user_service.get_user(
            tg_id=dto.user_tgid,
            username=dto.user_username,
        )

        if user is None:
            identificator = (
                f"<code>{dto.user_tgid}</code>"
                if dto.user_tgid
                else f"<b>@{dto.user_username}</b>"
            )
            return AddUserToTrackingResult(
                success=False,
                message=Dialog.UserTracking.USER_NOT_FOUND.format(
                    identificator=identificator
                ),
            )

        admin = await self._user_service.get_user(
            tg_id=dto.admin_tgid,
            username=dto.admin_username,
        )

        tracked_users = await self._user_tracking_repository.get_tracked_users_by_admin(
            admin_tgid=admin.tg_id,
        )

        tracked_user_ids = {u.id for u in tracked_users}
        if user.id in tracked_user_ids:
            return AddUserToTrackingResult(
                success=False,
                message=Dialog.UserTracking.USER_ALREADY_TRACKED.format(
                    user_username=user.username
                ),
            )

        try:
            await self._user_tracking_repository.add_user_to_tracking(
                admin_id=admin.id,
                user_id=user.id,
            )

            return AddUserToTrackingResult(
                success=True,
                message=Dialog.UserTracking.SUCCESS_ADD_USER_TO_TRACKING.format(
                    user_username=user.username,
                    user_tgid=user.tg_id,
                    admin_username=admin.username,
                ),
            )
        except Exception as e:
            logger.error(
                "Ошибка добавления в отслеживание: %s",
                e,
                exc_info=True,
            )
            return AddUserToTrackingResult(
                success=False,
                message=Dialog.UserTracking.ERROR_ADD_USER_TO_TRACKING,
            )
