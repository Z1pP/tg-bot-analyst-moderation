import logging

from aiogram import F, Router, types
from punq import Container

from constants import Dialog
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
            username = user.username or user.first_name or f"user_{user.id}"

            if user.is_bot:
                if user.id == message.bot.id:
                    logger.info(
                        f"Наш бот добавлен в группу '{chat_title}' (ID: {message.chat.id})"
                    )
                else:
                    logger.info(f"Бот {username} добавлен в группу '{chat_title}'")
            else:
                logger.info(
                    f"Пользователь {username} (ID: {user.id}) добавлен в группу '{chat_title}'"
                )

                # Проверка антиботом
                restrict_usecase: RestrictNewMemberUseCase = container.resolve(
                    RestrictNewMemberUseCase
                )
                bot_info = await message.bot.get_me()
                verify_link, custom_welcome = await restrict_usecase.execute(
                    chat_tgid=str(message.chat.id),
                    user_id=user.id,
                    bot_username=bot_info.username,
                )

                if verify_link:
                    username_val = user.username or user.first_name or str(user.id)

                    if custom_welcome:
                        try:
                            greeting_text = custom_welcome.format(username=username_val)
                        except (KeyError, ValueError):
                            greeting_text = custom_welcome
                    else:
                        greeting_text = Dialog.Antibot.GREETING.format(
                            username=username_val
                        )

                    greeting_template = (
                        greeting_text
                        + Dialog.Antibot.VERIFIED_LINK.format(link=verify_link)
                    )

                    await message.answer(
                        text=greeting_template,
                        parse_mode="HTML",
                    )

        logger.info(
            f"Обработка {len(message.new_chat_members)} новых участников завершена"
        )

    except Exception as e:
        await handle_exception(message, e, "process_new_chat_members")
