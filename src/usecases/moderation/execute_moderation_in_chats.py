"""Применение модерации (бан или варн) к пользователю сразу в нескольких чатах (админ-панель)."""

import logging
from typing import Union

from constants.punishment import PunishmentActions as Actions
from dto import ModerationActionDTO
from dto.moderation import ExecuteModerationInChatsDTO, ModerationInChatsResultDTO
from utils.moderation import format_violator_display

from .give_ban_user import GiveUserBanUseCase
from .give_warn_user import GiveUserWarnUseCase

logger = logging.getLogger(__name__)


class ExecuteModerationInChatsUseCase:
    """
    Оркестрация модерации по списку чатов: для каждого чата вызывается соответствующий сценарий
    (бан или предупреждение). Ошибки в отдельных чатах не прерывают обработку остальных.
    """

    def __init__(
        self,
        give_ban_use_case: GiveUserBanUseCase,
        give_warn_use_case: GiveUserWarnUseCase,
    ) -> None:
        self._give_ban_use_case = give_ban_use_case
        self._give_warn_use_case = give_warn_use_case

    def _resolve_executor(
        self, action: Actions
    ) -> Union[GiveUserBanUseCase, GiveUserWarnUseCase]:
        if action == Actions.BAN:
            return self._give_ban_use_case
        if action == Actions.WARNING:
            return self._give_warn_use_case
        raise ValueError(
            f"Неподдерживаемое действие модерации для пакетного режима: {action}"
        )

    async def execute(
        self, dto: ExecuteModerationInChatsDTO
    ) -> ModerationInChatsResultDTO:
        executor = self._resolve_executor(dto.action)
        success_titles: list[str] = []
        failed_titles: list[str] = []

        user_display = format_violator_display(dto.violator_username, dto.violator_tgid)
        logger.info(
            "Начало действия %s пользователя %s в %s чатах",
            dto.action.value,
            user_display,
            len(dto.chats),
        )

        for chat in dto.chats:
            moderation_dto = ModerationActionDTO(
                action=dto.action,
                violator_tgid=dto.violator_tgid,
                violator_username=dto.violator_username or "",
                admin_tgid=dto.admin_tgid,
                admin_username=dto.admin_username or "",
                chat_tgid=chat.tg_id,
                chat_title=chat.title,
                reason=dto.reason,
                from_admin_panel=True,
            )
            try:
                await executor.execute(dto=moderation_dto)
                success_titles.append(chat.title)
                logger.info(
                    "Действие %s в чате %s успешно",
                    dto.action.value,
                    chat.title,
                )
            except Exception as e:
                failed_titles.append(chat.title)
                logger.error(
                    "Ошибка действия %s в чате %s: %s",
                    dto.action.value,
                    chat.title,
                    e,
                    exc_info=True,
                )

        return ModerationInChatsResultDTO(
            success_chats_titles=tuple(success_titles),
            failed_chats_titles=tuple(failed_titles),
        )
