import logging

from aiogram import Bot, F, Router, types
from aiogram.enums import ChatType
from aiogram.filters import IS_MEMBER, IS_NOT_MEMBER, ChatMemberUpdatedFilter
from punq import Container

from constants import Dialog
from exceptions.base import BotBaseException
from keyboards.inline.chats import hide_notification_ikb
from tasks.moderation_tasks import delete_welcome_message_task
from usecases.archive import NotifyArchiveChatNewMemberUseCase
from usecases.moderation import RestrictNewMemberUseCase

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.chat_member(
    ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER),
    F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP]),
)
async def process_chat_member_joined(
    event: types.ChatMemberUpdated,
    container: Container,
    bot: Bot,
) -> None:
    """Обработчик входа нового участника в группу (ChatMemberUpdated)."""
    try:
        chat_title = event.chat.title or "Неизвестная группа"
        user = event.new_chat_member.user

        logger.info(
            "Новый участник в группе '%s': %s (ID: %s)",
            chat_title,
            user.username or user.first_name,
            user.id,
        )

        await _handle_new_member(
            chat=event.chat,
            user=user,
            bot=bot,
            container=container,
            chat_title=chat_title,
        )

    except BotBaseException as e:
        logger.warning(
            "Обработано исключение в process_chat_member_joined: %s",
            e,
            exc_info=True,
        )
        await bot.send_message(
            chat_id=event.chat.id,
            text=e.get_user_message(),
            parse_mode="HTML",
            reply_markup=hide_notification_ikb(),
        )
    except Exception as e:
        logger.error(
            "Необработанное исключение в process_chat_member_joined: %s",
            e,
            exc_info=True,
        )
        await bot.send_message(
            chat_id=event.chat.id,
            text="❌ Произошла непредвиденная ошибка. Попробуйте позже.",
            parse_mode="HTML",
            reply_markup=hide_notification_ikb(),
        )


async def _notify_archive(
    container: Container,
    chat_id: int,
    user_id: int,
    username: str | None,
    chat_title: str,
) -> None:
    """Уведомление в архивный чат о новом участнике."""
    notify_archive_usecase: NotifyArchiveChatNewMemberUseCase = container.resolve(
        NotifyArchiveChatNewMemberUseCase
    )
    await notify_archive_usecase.execute(
        chat_tgid=str(chat_id),
        user_tgid=user_id,
        username=username,
        chat_title=chat_title,
    )


def _get_formatted_welcome_text(
    welcome_text: str | None,
    username: str,
) -> str:
    """Форматирование текста приветствия."""
    if not welcome_text:
        return Dialog.Antibot.GREETING.format(username=username)

    try:
        return welcome_text.format(username=username)
    except (KeyError, ValueError):
        return welcome_text


async def _handle_new_member(
    chat: types.Chat,
    user: types.User,
    bot: Bot,
    container: Container,
    chat_title: str,
) -> None:
    """Обработка одного нового участника."""
    username = user.username or user.first_name or f"user_{user.id}"

    if user.is_bot:
        bot_info = await bot.get_me()
        if user.id == bot_info.id:
            logger.info(
                "Наш бот добавлен в группу '%s' (ID: %s)",
                chat_title,
                chat.id,
            )
        else:
            logger.info("Бот %s добавлен в группу '%s'", username, chat_title)
        return

    logger.info(
        "Пользователь %s (ID: %s) добавлен в группу '%s'",
        username,
        user.id,
        chat_title,
    )

    # 1. Уведомление в архивный чат
    logger.debug(
        "Вызов _notify_archive: chat_id=%s, user_id=%s, username=%s, chat_title=%s",
        chat.id,
        user.id,
        user.username,
        chat_title,
    )
    await _notify_archive(
        container=container,
        chat_id=chat.id,
        user_id=user.id,
        username=user.username,
        chat_title=chat_title,
    )

    # 2. Проверка антиботом и приветствие
    restrict_usecase: RestrictNewMemberUseCase = container.resolve(
        RestrictNewMemberUseCase
    )
    bot_info = await bot.get_me()
    restriction_data = await restrict_usecase.execute(
        chat_tgid=str(chat.id),
        user_id=user.id,
        bot_username=bot_info.username,
    )

    username_val = user.username or user.first_name or str(user.id)

    # Сценарий 1 и 3: Антибот включен
    if restriction_data.is_antibot_enabled and restriction_data.verify_link:
        greeting_text = ""
        if restriction_data.show_welcome_text:
            greeting_text = _get_formatted_welcome_text(
                welcome_text=restriction_data.welcome_text,
                username=username_val,
            )

        greeting_template = greeting_text + Dialog.Antibot.VERIFIED_LINK.format(
            link=restriction_data.verify_link
        )

        sent_message = await bot.send_message(
            chat_id=chat.id,
            text=greeting_template,
            parse_mode="HTML",
        )

        if restriction_data.auto_delete_welcome_text:
            await delete_welcome_message_task.kiq(
                chat_id=chat.id,
                message_id=sent_message.message_id,
                delay_seconds=3600,
            )

    # Сценарий 2: Антибот выключен, но приветствие включено
    elif not restriction_data.is_antibot_enabled and restriction_data.show_welcome_text:
        greeting_text = _get_formatted_welcome_text(
            welcome_text=restriction_data.welcome_text,
            username=username_val,
        )

        sent_message = await bot.send_message(
            chat_id=chat.id,
            text=greeting_text,
            parse_mode="HTML",
        )

        if restriction_data.auto_delete_welcome_text:
            await delete_welcome_message_task.kiq(
                chat_id=chat.id,
                message_id=sent_message.message_id,
                delay_seconds=3600,
            )
