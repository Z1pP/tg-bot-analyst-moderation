"""Use case: получение отчёта о правах бота в чате."""

import html
import logging
from typing import Literal, Optional

from aiogram.types import ChatMemberAdministrator, ChatMemberOwner
from pydantic import BaseModel, ConfigDict

from dto.chat_dto import GetChatWithArchiveDTO
from services.permissions import BotPermissionService
from usecases.chat import GetChatWithArchiveUseCase

logger = logging.getLogger(__name__)


class GetBotPermissionsResult(BaseModel):
    """Результат проверки прав: либо текст отчёта, либо ключ ошибки для UI."""

    success: bool
    text: Optional[str] = None
    error_key: Optional[Literal["chat_not_found", "permissions_error"]] = None

    model_config = ConfigDict(frozen=True)

STATUS_NAMES = {
    "creator": "Создатель",
    "administrator": "Администратор",
    "member": "Участник",
    "restricted": "Ограничен",
    "left": "Покинул чат",
    "kicked": "Заблокирован",
}

ADMIN_PERMISSIONS_GROUP = [
    (
        "can_delete_messages",
        "Удаление сообщений",
        "удаляет сообщения нарушителей при варне/бане",
        "не удалит сообщения при модерации и в админ-панели",
    ),
    (
        "can_restrict_members",
        "Блокировка и мут пользователей",
        "антибот и модерация (/warn, /ban) работают",
        "антибот и /warn, /ban не сработают",
    ),
    (
        "can_invite_users",
        "Создание приглашений",
        "генерирует ссылку для верификации в антиботе",
        "не создаст ссылку для верификации новых участников",
    ),
    (
        "can_manage_chat",
        "Управление чатом",
        "базовые админ-действия доступны",
        "ограничены админ-действия",
    ),
    (
        "can_pin_messages",
        "Закрепление сообщений",
        "может закреплять сообщения",
        "не сможет закреплять",
    ),
    (
        "can_promote_members",
        "Повышение до администратора",
        "может назначать администраторов",
        "не может назначать администраторов",
    ),
    (
        "can_change_info",
        "Изменение информации чата",
        "может менять название и описание",
        "не может менять название и описание",
    ),
    (
        "can_manage_topics",
        "Управление темами",
        "может управлять темами в форуме",
        "не может управлять темами",
    ),
]

ADMIN_PERMISSIONS_CHANNEL = [
    (
        "can_post_messages",
        "Отправка сообщений",
        "отправляет ежедневные отчёты в архив",
        "не отправит отчёты в архивный канал",
    ),
    (
        "can_edit_messages",
        "Редактирование сообщений других",
        "может редактировать сообщения в канале",
        "не может редактировать чужие сообщения",
    ),
]


def _build_permission_lines(member, is_channel: bool) -> list[str]:
    """Строит список строк с правами (✅/❌) и пояснениями."""
    if isinstance(member, ChatMemberOwner):
        return ["✅ Все права (создатель)"]

    if not isinstance(member, ChatMemberAdministrator):
        return []

    lines = []
    permissions = list(ADMIN_PERMISSIONS_GROUP)
    if is_channel:
        permissions = permissions + list(ADMIN_PERMISSIONS_CHANNEL)

    for item in permissions:
        attr, name, explain_has, explain_missing = item
        has_right = getattr(member, attr, False)
        icon = "✅" if has_right else "❌"
        explanation = explain_has if has_right else explain_missing
        lines.append(f"{icon} {name}\n   <i>{explanation}</i>")

    return lines


def _format_report(chat_title: str, status: str, permission_lines: list[str]) -> str:
    """Формирует текст отчёта о правах бота."""
    status_name = STATUS_NAMES.get(status, status)
    title_escaped = html.escape(chat_title or "Без названия")

    lines = [
        f"🔍 Права бота в чате «{title_escaped}»",
        "",
        f"📋 Статус: <b>{status_name}</b>",
        "",
    ]

    if permission_lines:
        lines.append("Права администратора (пояснение — что может/не может бот):")
        lines.extend(permission_lines)
    else:
        lines.append("Нет прав администратора.")

    return "\n".join(lines)


class GetBotPermissionsInChatUseCase:
    """Возвращает текст отчёта о правах бота в чате."""

    def __init__(
        self,
        get_chat_with_archive: GetChatWithArchiveUseCase,
        bot_permission_service: BotPermissionService,
    ) -> None:
        self._get_chat = get_chat_with_archive
        self._permission_service = bot_permission_service

    async def execute(self, chat_id: int) -> GetBotPermissionsResult:
        """
        Строит отчёт о правах бота в чате.

        Args:
            chat_id: ID чата (БД).

        Returns:
            GetBotPermissionsResult: success + text отчёта либо error_key для UI.
        """
        chat = await self._get_chat.execute(GetChatWithArchiveDTO(chat_id=chat_id))
        if not chat:
            return GetBotPermissionsResult(
                success=False, error_key="chat_not_found"
            )

        member = await self._permission_service.get_bot_member(
            chat_tgid=chat.chat_id
        )
        if member is None:
            return GetBotPermissionsResult(
                success=False, error_key="permissions_error"
            )

        is_channel = await self._permission_service.is_channel(chat.chat_id)
        permission_lines = _build_permission_lines(member, is_channel=is_channel)
        text = _format_report(
            chat_title=chat.title,
            status=member.status,
            permission_lines=permission_lines,
        )
        return GetBotPermissionsResult(success=True, text=text)
