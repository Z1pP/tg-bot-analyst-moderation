import logging
import re
from typing import List, Optional

from aiogram import F, Router
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputMediaAnimation,
    InputMediaDocument,
    InputMediaPhoto,
    InputMediaVideo,
    InputTextMessageContent,
    Message,
)

from container import container
from filters import StaffOnlyInlineFilter
from models import MessageTemplate
from repositories import MessageTemplateRepository

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.inline_query(
    F.query,
    StaffOnlyInlineFilter(),
)
async def handle_inline_query(query: InlineQuery) -> None:
    """Обработчик inline запросов"""
    try:
        variants = await get_variants(query.query)
        results = []

        for variant in variants:
            cleaned_content = remove_html_tags(variant.content)
            results.append(
                InlineQueryResultArticle(
                    id=str(variant.id),
                    title=variant.title,
                    description=short_the_text(cleaned_content),
                    input_message_content=InputTextMessageContent(
                        message_text=f"🔸TEMPLATE__{variant.id}",
                        parse_mode="HTML",
                    ),
                )
            )

        await query.answer(results, cache_time=1)
    except Exception as e:
        logger.error(f"Ошибка при обработке inline запроса: {e}")
        # Отправляем пустой результат в случае ошибки
        await query.answer([], cache_time=1)


def remove_html_tags(text: str) -> str:
    """Удаляет HTML-теги из строки."""
    if not text:
        return ""
    return re.sub(r"<[^>]+>", "", text)


def short_the_text(text: str, length: int = 75) -> str:
    """Сокращаем описание"""
    if not text:
        return ""
    return text[:length] + "..." if len(text) > length else text


@router.message(F.text.startswith("🔸TEMPLATE__"))
async def handle_template_message(message: Message) -> None:
    """Обработчик сообщений с маркером шаблона"""
    try:
        # Извлекаем ID шаблона
        template_id = int(message.text.replace("🔸TEMPLATE__", ""))
        chat_id = str(message.chat.id)

        reply_message_id = (
            message.reply_to_message.message_id if message.reply_to_message else None
        )

        # Сохраняем сообщение модератора
        await save_moderator_message(message)

        # Удаляем сообщение с маркером
        await message.delete()

        # Отправляем шаблон
        await send_template(
            message=message,
            template_id=template_id,
            reply_message_id=reply_message_id,
            chat_id=chat_id,
        )

    except Exception as e:
        logger.error(f"Ошибка при отправке шаблона сообщения: {e}")


async def send_template(
    message: Message,
    template_id: int,
    chat_id: str,
    reply_message_id: Optional[int],
) -> None:
    """Отправляет ответ по шаблону"""
    template_repo: MessageTemplateRepository = container.resolve(
        MessageTemplateRepository
    )

    template = await template_repo.get_template_and_increase_usage_count(
        template_id=template_id,
        chat_id=chat_id,
    )

    if not template:
        return

    if template.media_items:
        await send_media_group(
            message=message,
            template=template,
            reply_message_id=reply_message_id,
        )
    else:
        await message.bot.send_message(
            chat_id=message.chat.id,
            text=template.content,
            reply_to_message_id=reply_message_id,
            parse_mode="HTML",
        )


async def send_media_group(
    message: Message,
    template: MessageTemplate,
    reply_message_id: Optional[int],
) -> None:
    """Отправляет медиа-группу"""
    try:

        media_group = []
        media_types = {
            "photo": InputMediaPhoto,
            "video": InputMediaVideo,
            "animation": InputMediaAnimation,
            "document": InputMediaDocument,
        }

        # Создаем медиа группу
        for i, media in enumerate(template.media_items):
            try:
                # Проверяем файл на доступолность
                await message.bot.get_file(file_id=media.file_id)

                media_class = media_types.get(media.media_type)
                if media_class:
                    media_group.append(
                        media_class(
                            media=media.file_id,
                            caption=template.content if i == 0 else None,
                            parse_mode="HTML" if i == 0 else None,
                        )
                    )
            except Exception as e:
                logger.error(f"Файл {media.file_id} недоступен: {e}")
                continue

        if media_group:
            await message.bot.send_media_group(
                chat_id=message.chat.id,
                media=media_group,
                reply_to_message_id=reply_message_id,
            )
        else:
            await message.bot.send_message(
                chat_id=message.chat.id,
                text=f"{template.content}\n\n⚠️ Медиафайлы временно недоступны",
                reply_to_message_id=reply_message_id,
                parse_mode="HTML",
            )
    except Exception as e:
        logger.error(f"Ошибка при отправке медиа-группы: {e}")
        # Отправляем только текст в случае ошибки
        await message.bot.send_message(
            chat_id=message.chat.id,
            text=template.content,
            reply_to_message_id=reply_message_id,
            parse_mode="HTML",
        )


async def get_variants(query: str) -> List[MessageTemplate]:
    """Получает варианты шаблонов по запросу"""
    template_repo: MessageTemplateRepository = container.resolve(
        MessageTemplateRepository
    )
    templates = await template_repo.get_templates_by_query(query=query)

    # Сортируем шаблоны по количеству исользований от большего к меньшему
    sorted_templates = list(sorted(templates, key=lambda x: -x.usage_count))

    return sorted_templates


async def save_moderator_message(message: Message) -> None:
    """Сохраняет сообщение модератора в БД"""
    from .message_handler import group_message_handler

    await group_message_handler(message)
