import logging

from aiogram import F, Router, types
from punq import Container

from constants import Dialog
from tasks.moderation_tasks import delete_welcome_message_task
from usecases.archive import NotifyArchiveChatNewMemberUseCase
from usecases.moderation import RestrictNewMemberUseCase
from utils.exception_handler import handle_exception

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.message(F.new_chat_members)
async def process_new_chat_members(message: types.Message, container: Container):
    """Обработчик добавления новых участников в группу."""
    try:
        chat_title = message.chat.title or "Неизвестная группа"
        logger.info(
            f"Новые участники в группе '{chat_title}': {len(message.new_chat_members)}"
        )

        for user in message.new_chat_members:
            await _handle_new_member(
                message=message,
                user=user,
                container=container,
                chat_title=chat_title,
            )

        logger.info(
            f"Обработка {len(message.new_chat_members)} новых участников завершена"
        )

    except Exception as e:
        await handle_exception(message, e, "process_new_chat_members")


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
    message: types.Message,
    user: types.User,
    container: Container,
    chat_title: str,
) -> None:
    """Обработка одного нового участника."""
    username = user.username or user.first_name or f"user_{user.id}"

    if user.is_bot:
        if user.id == message.bot.id:
            logger.info(
                f"Наш бот добавлен в группу '{chat_title}' (ID: {message.chat.id})"
            )
        else:
            logger.info(f"Бот {username} добавлен в группу '{chat_title}'")
        return

    logger.info(
        f"Пользователь {username} (ID: {user.id}) добавлен в группу '{chat_title}'"
    )

    # 1. Уведомление в архивный чат
    await _notify_archive(
        container=container,
        chat_id=message.chat.id,
        user_id=user.id,
        username=user.username,
        chat_title=chat_title,
    )

    # 2. Проверка антиботом и приветствие
    restrict_usecase: RestrictNewMemberUseCase = container.resolve(
        RestrictNewMemberUseCase
    )
    bot_info = await message.bot.get_me()
    restriction_data = await restrict_usecase.execute(
        chat_tgid=str(message.chat.id),
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

        sent_message = await message.answer(text=greeting_template, parse_mode="HTML")

        if restriction_data.auto_delete_welcome_text:
            await delete_welcome_message_task.kiq(
                chat_id=message.chat.id,
                message_id=sent_message.message_id,
                delay_seconds=3600,
            )

    # Сценарий 2: Антибот выключен, но приветствие включено
    elif not restriction_data.is_antibot_enabled and restriction_data.show_welcome_text:
        greeting_text = _get_formatted_welcome_text(
            welcome_text=restriction_data.welcome_text,
            username=username_val,
        )

        sent_message = await message.answer(text=greeting_text, parse_mode="HTML")

        if restriction_data.auto_delete_welcome_text:
            await delete_welcome_message_task.kiq(
                chat_id=message.chat.id,
                message_id=sent_message.message_id,
                delay_seconds=3600,
            )
