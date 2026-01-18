import logging
from typing import Optional

from constants.enums import AdminActionType, UserRole
from models import User
from services import AdminActionLogService, UserService

logger = logging.getLogger(__name__)


class UpdateUserRoleUseCase:
    def __init__(
        self,
        user_service: UserService,
        admin_action_log_service: AdminActionLogService,
    ):
        self._user_service = user_service
        self._admin_action_log_service = admin_action_log_service

    async def execute(
        self, user_id: int, new_role: UserRole, admin_tg_id: str
    ) -> Optional[User]:
        user = await self._user_service.get_user_by_id(user_id=user_id)
        if not user:
            return None

        old_role = user.role
        updated_user = await self._user_service.update_user_role(
            user_id=user_id, new_role=new_role
        )

        if updated_user:
            # Логируем действие администратора
            target_username = updated_user.username or f"ID:{updated_user.tg_id}"
            details = (
                f"Пользователь: @{target_username} ({updated_user.id}), "
                f"Роль: {old_role.value} -> {new_role.value}"
            )
            await self._admin_action_log_service.log_action(
                admin_tg_id=admin_tg_id,
                action_type=AdminActionType.UPDATE_PERMISSIONS,
                details=details,
            )

        return updated_user
