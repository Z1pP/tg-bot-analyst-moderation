import logging
from typing import Optional

from aiogram import F, Router, types
from aiogram.filters import Command

from constants.punishment import PunishmentActions as Actions
from constants.punishment import PunishmentText
from container import container
from dto import ModerationActionDTO
from filters.admin_filter import StaffOnlyFilter
from usecases.moderation.give_warn_user import GiveUserWarnUseCase

router = Router(name=__name__)


@router.message(
    Command("warn"),
    StaffOnlyFilter(),
    F.reply_to_message,
)
async def warn_user_handler(message: types.Message) -> None:
    """
    Обрабатывает команду /warn предупреждения пользователя в общем чате
    """

    reason = get_reason(message=message)

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

    await message.delete()


# @router.message(
#     Command("ban"),
#     StaffOnlyFilter(),
#     F.reply_to_message,
# )
# async def ban_user_handler(message: types.Message) -> None:
#     """
#     Обрабатывает команду /ban чтобы заблокировать пользователя
#     """
#     if message.from_user.id == message.reply_to_message.from_user.id:
#         logging.info("Попытка забанить самого себя от %s", message.from_user.id)
#         return

#     reason = get_reason(message)

#     if not reason:
#         reason = PunishmentText.WARNING_TEXT

#     user_to_ban = message.reply_to_message.from_user.id
#     chat_id = message.chat.id

#     await message.bot.forward_message(
#         chat_id=message.from_user.id,
#         from_chat_id=chat_id,
#         message_id=message.reply_to_message.message_id,
#     )
#     await message.delete()


def get_reason(message: types.Message) -> Optional[str]:
    """Извлекает текст причины блокироки или предупреждения или None"""
    parts = message.text.split(maxsplit=1)

    if len(parts) > 1:
        return parts[1]
    return None


# async def forward_and_send_msg(dto: ModerationActionDTO) -> None:
#     """
#     Пересылает сообщение пользователя и отправляет текстовое уведомление
#     """

#     new_msg = None

#     try:
#         await dto.message.bot.forward_message(
#             chat_id=dto.moderator_tg_id,
#             from_chat_id=dto.chat_tg_id,
#             message_id=dto.message.reply_to_message.message_id,
#         )
#     except Exception as e:
#         logging.exception("Ошибка при копировании сообщения: %s", e)
#         await message.bot.send_message(
#             chat_id=user_tg_id,
#             text="⚠️ Не удалось скопировать сообщение пользователя.",
#         )

#     try:
#         await message.bot.send_message(
#             chat_id=user_tg_id,
#             text=msg_text,
#             reply_markup=cancel_moderation_kb(
#                 action=action, user_id=user_id, chat_id=chat_id
#             ),
#             reply_to_message_id=new_msg.message_id if new_msg else None,
#         )
#     except Exception as e:
#         logging.exception("Ошибка при отправке сообщения: %s", e)
#         await message.bot.send_message(
#             chat_id=user_tg_id,
#             text="⚠️ Не удалось отправить текстовое уведомление.",
#         )
