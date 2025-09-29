import logging
from typing import Optional

from aiogram import F, Router, types
from aiogram.filters import Command

from constants.punishment import PunishmentActions as Actions
from container import container
from dto import ModerationActionDTO
from filters.admin_filter import StaffOnlyFilter
from usecases.moderation import GiveUserBanUseCase, GiveUserWarnUseCase

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.message(
    Command("warn"),
    StaffOnlyFilter(),
    F.reply_to_message,
)
async def warn_user_handler(message: types.Message) -> None:
    """
    Обрабатывает команду /warn предупреждения пользователя в общем чате
    """

    reason = extract_reason_from_message(message=message)

    dto = ModerationActionDTO(
        action=Actions.WARNING,
        user_reply_tgid=str(message.reply_to_message.from_user.id),
        user_reply_username=message.reply_to_message.from_user.username,
        admin_username=message.from_user.username,
        admin_tgid=str(message.from_user.id),
        chat_tgid=str(message.chat.id),
        chat_title=message.chat.title,
        reply_message_id=message.reply_to_message.message_id,
        reason=reason,
    )

    usecase: GiveUserWarnUseCase = container.resolve(GiveUserWarnUseCase)
    await usecase.execute(dto=dto)

    logger.info(
        "Админ %s выдал предупреждение пользователю %s в чате %s",
        dto.admin_username,
        dto.user_reply_username,
        dto.chat_title,
    )

    await message.delete()


@router.message(
    Command("ban"),
    StaffOnlyFilter(),
    F.reply_to_message,
)
async def ban_user_handler(message: types.Message) -> None:
    """
    Обрабатывает команду /ban чтобы заблокировать пользователя
    """
    reason = extract_reason_from_message(message=message)

    dto = ModerationActionDTO(
        action=Actions.BAN,
        user_reply_tgid=str(message.reply_to_message.from_user.id),
        user_reply_username=message.reply_to_message.from_user.username,
        admin_username=message.from_user.username,
        admin_tgid=str(message.from_user.id),
        chat_tgid=str(message.chat.id),
        chat_title=message.chat.title,
        reply_message_id=message.reply_to_message.message_id,
        reason=reason,
    )

    usecase: GiveUserBanUseCase = container.resolve(GiveUserBanUseCase)
    await usecase.execute(dto=dto)

    logger.info(
        "Админ %s забанил пользователя %s в чате %s",
        dto.admin_username,
        dto.user_reply_username,
        dto.chat_title,
    )

    await message.delete()


def extract_reason_from_message(message: types.Message) -> Optional[str]:
    """Извлекает текст причины блокироки или предупреждения или None"""
    parts = message.text.split(maxsplit=1)

    if len(parts) > 1:
        return parts[1]
    return None
