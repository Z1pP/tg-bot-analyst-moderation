"""Обработчик проверки прав бота в чате через Telegram API."""

import html
import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from keyboards.inline.chats import (
    back_to_chat_actions_only_ikb,
    chat_actions_ikb,
    chats_menu_ikb,
)
from services.chat import ChatService
from services.permissions import BotPermissionService
from states import ChatStateManager
from utils.send_message import safe_edit_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)

# Маппинг статусов участника на человекопонятные названия
STATUS_NAMES = {
    "creator": "Создатель",
    "administrator": "Администратор",
    "member": "Участник",
    "restricted": "Ограничен",
    "left": "Покинул чат",
    "kicked": "Заблокирован",
}

# Права администратора: (атрибут, название, пояснение при наличии, пояснение при отсутствии)
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

# Дополнительные права для каналов
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


def _format_permissions_report(
    chat_title: str,
    status: str,
    permission_lines: list[str],
) -> str:
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


def _build_permission_lines(member, is_channel: bool) -> list[str]:
    """Строит список строк с правами (✅/❌) и пояснениями."""
    from aiogram.types import ChatMemberAdministrator, ChatMemberOwner

    if isinstance(member, ChatMemberOwner):
        return ["✅ Все права (создатель)"]

    if not isinstance(member, ChatMemberAdministrator):
        return []

    lines = []
    permissions = list(ADMIN_PERMISSIONS_GROUP)
    if is_channel:
        permissions.extend(ADMIN_PERMISSIONS_CHANNEL)

    for item in permissions:
        attr, name, explain_has, explain_missing = item
        has_right = getattr(member, attr, False)
        icon = "✅" if has_right else "❌"
        explanation = explain_has if has_right else explain_missing
        lines.append(f"{icon} {name}\n   <i>{explanation}</i>")

    return lines


async def _get_chat_type(bot, chat_tgid: str) -> bool:
    """Возвращает True если чат — канал."""
    try:
        chat = await bot.get_chat(chat_id=chat_tgid)
        return chat.type == "channel"
    except Exception:
        return False


@router.callback_query(
    F.data == CallbackData.Chat.CHECK_PERMISSIONS,
    ChatStateManager.selecting_chat,
)
async def check_permissions_handler(
    callback: CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    """
    Обработчик проверки прав бота в чате.
    Запрашивает данные через Telegram API и выводит подробный отчёт.
    """
    await callback.answer()

    chat_id = await state.get_value("chat_id")
    if chat_id is None:
        logger.warning("chat_id не найден в state при проверке прав")
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Chat.CHAT_NOT_SELECTED,
            reply_markup=chats_menu_ikb(),
        )
        return

    chat_service: ChatService = container.resolve(ChatService)
    chat = await chat_service.get_chat_with_archive(chat_id=chat_id)

    if not chat:
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Chat.CHAT_NOT_FOUND_OR_ALREADY_REMOVED,
            reply_markup=chat_actions_ikb(),
        )
        return

    bot_permission_service: BotPermissionService = container.resolve(
        BotPermissionService
    )
    member = await bot_permission_service.get_bot_member(chat_tgid=chat.chat_id)

    if member is None:
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Chat.PERMISSIONS_CHECK_ERROR,
            reply_markup=back_to_chat_actions_only_ikb(),
        )
        return

    is_channel = await _get_chat_type(callback.bot, chat.chat_id)
    permission_lines = _build_permission_lines(member, is_channel=is_channel)
    text = _format_permissions_report(
        chat_title=chat.title,
        status=member.status,
        permission_lines=permission_lines,
    )

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=text,
        reply_markup=back_to_chat_actions_only_ikb(),
    )
