import logging

from aiogram import Bot, F, Router, types
from aiogram.enums import ChatType
from aiogram.filters import IS_MEMBER, IS_NOT_MEMBER, ChatMemberUpdatedFilter
from aiogram.types import ChatMemberBanned
from punq import Container

from constants.enums import MembershipEventType
from dto import ArchiveMemberNotificationDTO
from dto.membership_event import RecordChatMembershipEventDTO
from usecases.archive import (
    NotifyArchiveChatMemberKickedUseCase,
    NotifyArchiveChatMemberLeftUseCase,
)
from usecases.membership import RecordChatMembershipEventUseCase

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.chat_member(
    ChatMemberUpdatedFilter(IS_MEMBER >> IS_NOT_MEMBER),
    F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP]),
)
async def process_chat_member_left(
    event: types.ChatMemberUpdated,
    container: Container,
    bot: Bot,
) -> None:
    """Обработчик выхода участника из группы (ChatMemberUpdated)."""
    try:
        chat_title = event.chat.title or "Неизвестная группа"
        left_user = event.old_chat_member.user
        username = left_user.username or left_user.first_name or f"user_{left_user.id}"

        if not left_user.is_bot:
            record_uc: RecordChatMembershipEventUseCase = container.resolve(
                RecordChatMembershipEventUseCase
            )
            leave_kind = (
                MembershipEventType.REMOVED
                if isinstance(event.new_chat_member, ChatMemberBanned)
                else MembershipEventType.LEFT
            )
            await record_uc.execute(
                RecordChatMembershipEventDTO(
                    chat_tgid=str(event.chat.id),
                    user_tgid=left_user.id,
                    event_type=leave_kind,
                )
            )

        if left_user.is_bot:
            bot_info = await bot.get_me()
            if left_user.id == bot_info.id:
                logger.info(
                    "Наш бот удален из группы '%s' (ID: %s)",
                    chat_title,
                    event.chat.id,
                )
                return
            logger.info("Бот %s покинул группу '%s'", username, chat_title)
        else:
            logger.info(
                "Пользователь %s (ID: %s) покинул группу '%s'",
                username,
                left_user.id,
                chat_title,
            )

        # Кик: new_chat_member = ChatMemberBanned. Не дублируем уведомление,
        # если кикнул наш бот (задача kick_unverified_member_task уже уведомила).
        if isinstance(event.new_chat_member, ChatMemberBanned):
            bot_info = await bot.get_me()
            if event.from_user.id == bot_info.id:
                logger.info(
                    "Пользователь %s кикнут нашим ботом — уведомление уже отправлено задачей",
                    left_user.id,
                )
                return
            notify_usecase = container.resolve(NotifyArchiveChatMemberKickedUseCase)
        else:
            notify_usecase = container.resolve(NotifyArchiveChatMemberLeftUseCase)

        dto = ArchiveMemberNotificationDTO(
            chat_tgid=str(event.chat.id),
            user_tgid=left_user.id,
            username=username,
            chat_title=chat_title,
        )
        await notify_usecase.execute(dto)

    except Exception as e:
        logger.error(
            "Ошибка при обработке выхода участника из группы: %s", e, exc_info=True
        )
