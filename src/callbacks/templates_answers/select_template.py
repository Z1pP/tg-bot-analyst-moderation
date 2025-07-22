import logging
from typing import List

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InputMediaAnimation,
    InputMediaPhoto,
    InputMediaVideo,
    Message,
)

from container import container
from models import MessageTemplate, TemplateMedia
from repositories import MessageTemplateRepository
from states import TemplateStateManager

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(
    TemplateStateManager.listing_templates,
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

    await send_template(
        bot=bot,
        message=query.message,
        template_id=int(template_id),
    )

    await query.answer()


async def send_template(
    bot: Bot,
    message: Message,
    template_id: int,
) -> None:
    """Отправляет шаблон быстрого ответа пользователю"""
    template_repo: MessageTemplateRepository = container.resolve(
        MessageTemplateRepository
    )
    template = await template_repo.get_template_by_id(template_id=template_id)

    if not template:
        await message.reply("❌ Шаблон не найден")
        return

    media_items = template.media_items

    # Отправляем в зависимости от типа контента
    if not media_items:
        # Только текст
        await bot.send_message(
            chat_id=message.chat.id,
            text=template.content,
            parse_mode="HTML",
        )
    elif len(media_items) == 1:
        # Одно фото с текстом
        await send_single_media(message, template, media_items[0])
    else:
        # Группа медиа
        await send_media_group(bot, message, template, media_items)


async def send_single_media(
    message: Message,
    template: MessageTemplate,
    media: TemplateMedia,
) -> None:
    """Отправляет одиночный медиа файл с текстом"""

    try:
        if media.media_type == "photo":
            await message.reply_photo(
                photo=media.file_id,
                caption=template.content,
                parse_mode="HTML",
            )
        elif media.media_type == "document":
            await message.reply_document(
                document=media.file_id,
                caption=template.content,
                parse_mode="HTML",
            )
        elif media.media_type == "video":
            await message.reply_video(
                video=media.file_id,
                caption=template.content,
                parse_mode="HTML",
            )
        elif media.media_type == "animation":
            await message.reply_animation(
                animation=media.file_id,
                caption=template.content,
                parse_mode="HTML",
            )
    except Exception as e:
        logger.error(f"Ошибка при отправке шаблона: {e}")
        await message.reply(
            f"❌ Медиа недоступно. Текст шаблона:\n\n{template.content}",
            parse_mode="HTML",
        )


async def send_media_group(
    bot: Bot,
    message: Message,
    template: MessageTemplate,
    media_files: List[TemplateMedia],
) -> None:
    """Отправляет группу медиа файлов"""
    media_group = []

    # Создаем медиа группу
    for i, media in enumerate(media_files):
        if media.media_type == "photo":
            media_group.append(
                InputMediaPhoto(
                    media=media.file_id,
                    caption=template.content if i == 0 else None,
                    parse_mode="HTML" if i == 0 else None,
                )
            )
        elif media.media_type == "video":
            media_group.append(
                InputMediaVideo(
                    media=media.file_id,
                    caption=template.content if i == 0 else None,
                    parse_mode="HTML" if i == 0 else None,
                )
            )
        elif media.media_type == "animation":
            media_group.append(
                InputMediaAnimation(
                    media=media.file_id,
                    caption=template.content if i == 0 else None,
                    parse_mode="HTML" if i == 0 else None,
                )
            )

    # Отправляем группу
    if media_group:
        try:
            await bot.send_media_group(
                chat_id=message.chat.id,
                media=media_group,
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке медиа-группы: {e}")
            await message.reply(
                f"❌ Медиа недоступно. Текст шаблона:\n\n{template.content}",
                parse_mode="HTML",
            )
