from constants.enums import AdminActionType
from dto import RemoveUserTrackingDTO
from repositories import UserTrackingRepository
from services import AdminActionLogService, UserService


class RemoveUserFromTrackingUseCase:
    def __init__(
        self,
        user_tracking_repository: UserTrackingRepository,
        user_service: UserService,
        admin_action_log_service: AdminActionLogService,
    ):
        self.user_tracking_repository = user_tracking_repository
        self.user_service = user_service
        self.admin_action_log_service = admin_action_log_service

    async def execute(self, dto: RemoveUserTrackingDTO) -> bool:
        """Удаляет пользователя из списка отслеживания админа."""
        admin = await self.user_service.get_user(
            tg_id=dto.admin_tgid,
            username=dto.admin_username,
        )

        if not admin:
            return False

        # Получаем информацию о пользователе до удаления для логирования
        target_user = await self.user_service.get_user(
            tg_id=dto.user_tgid,
            username=dto.user_username,
        )

        if not target_user:
            return False

        await self.user_tracking_repository.remove_user_from_tracking(
            admin_id=admin.id,
            user_id=target_user.id,
        )

        if target_user:
            # Логируем действие администратора
            details = f"Пользователь: @{target_user.username} ({target_user.tg_id})"
            await self.admin_action_log_service.log_action(
                admin_tg_id=admin.tg_id,
                action_type=AdminActionType.REMOVE_USER,
                details=details,
            )

        return True
