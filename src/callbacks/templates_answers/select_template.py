import logging
from typing import List

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InputMediaPhoto, Message

from container import container
from models import QuickResponse, QuickResponseMedia
from repositories import QuickResponseRepository
from states.response_state import QuickResponseStateManager

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(
    QuickResponseStateManager.listing_templates,
    F.data.startswith("template__"),
)
async def select_template_callback(
    query: CallbackQuery,
    bot: Bot,
    state: FSMContext,
) -> None:
    """Обработчик выбора шаблона"""
    template_id = query.data.split("__")[1]

    logger.info(
        "Был выбран шаблон c ID:%d пользователем - %s",
        template_id,
        query.from_user.username,
    )

    await send_quick_response(
        bot=bot,
        message=query.message,
        response_id=int(template_id),
    )

    await query.answer()


async def send_quick_response(
    bot: Bot,
    message: Message,
    response_id: int,
) -> None:
    """Отправляет шаблон быстрого ответа пользователю"""
    response_repo = container.resolve(QuickResponseRepository)
    response = await response_repo.get_quick_response_by_id(response_id=response_id)

    if not response:
        await message.reply("❌ Шаблон не найден")
        return

    media_items = response.media_items

    # Отправляем в зависимости от типа контента
    if not media_items:
        # Только текст
        await bot.send_message(
            chat_id=message.chat.id,
            text=response.content,
            parse_mode="HTML",
        )
    elif len(media_items) == 1:
        # Одно фото с текстом
        await send_single_media(bot, message, response, media_items[0])
    else:
        # Группа медиа
        await send_media_group(bot, message, response, media_items)


async def send_single_media(
    bot: Bot, message: Message, response: QuickResponse, media: QuickResponseMedia
) -> None:
    """Отправляет одиночный медиа файл с текстом"""
    try:
        if media.media_type == "photo":
            await message.reply_photo(
                photo=media.file_id,
                caption=response.content,
                parse_mode="HTML",
            )
        elif media.media_type == "document":
            await bot.send_document(
                document=media.file_id,
                caption=response.content,
                parse_mode="HTML",
            )
    except Exception:
        await message.reply(
            f"❌ Медиа недоступно. Текст шаблона:\n\n{response.content}",
            parse_mode="HTML",
        )


async def send_media_group(
    bot: Bot,
    message: Message,
    response: QuickResponse,
    media_files: List[QuickResponseMedia],
) -> None:
    """Отправляет группу медиа файлов"""
    media_group = []

    # Создаем медиа группу
    for i, media in enumerate(media_files):
        if media.media_type == "photo":
            media_group.append(
                InputMediaPhoto(
                    media=media.file_id,
                    caption=response.content if i == 0 else None,
                    parse_mode="HTML" if i == 0 else None,
                )
            )

    # Отправляем группу
    if media_group:
        try:
            await bot.send_media_group(chat_id=message.chat.id, media=media_group)
        except Exception:
            await message.reply(
                f"❌ Медиа недоступно. Текст шаблона:\n\n{response.content}",
                parse_mode="HTML",
            )
