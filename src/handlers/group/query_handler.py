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
                    message_text=f"🔸TEMPLATE_{variant.id}🔸\n{variant.title}",
                    parse_mode="HTML",
                ),
            )
        )

    await query.answer(results, cache_time=1)


def remove_html_tags(text: str) -> str:
    """Удаляет HTML-теги из строки."""
    return re.sub(r"<[^>]+>", "", text)


def short_the_text(text: str, length: int = 75):
    """Сокращаем описание"""
    return text[:length] + "..." if len(text) > length else text


@router.message(F.text.startswith("🔸TEMPLATE_"))
async def handle_template_message(message: Message) -> None:
    """Обработчик сообщений с маркером шаблона"""
    try:
        # Извлекаем ID шаблона
        template_id = int(message.text.split("_")[1].split("🔸")[0])
        reply_message_id = (
            message.reply_to_message.message_id if message.reply_to_message else None
        )

        # Сохраняем сообщение модератора
        await save_moderator_message(message)

        # Удаляем сообщение с маркером
        await message.delete()

        # Отправляем шаблон
        await send_template_response(message, template_id, reply_message_id)

    except Exception as e:
        logger.error(f"Error handling template message: {e}")


async def send_template_response(
    message: Message,
    template_id: int,
    reply_message_id: Optional[int],
) -> None:
    """Отправляет ответ по шаблону"""
    response_repo: MessageTemplateRepository = container.resolve(
        MessageTemplateRepository
    )
    template = await response_repo.get_template_by_id(template_id)

    # template = await update_template_usage_count(
    #     template_id=template.id,
    #     respository=response_repo,
    # )

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


async def update_template_usage_count(
    template_id: int,
    respository: MessageTemplateRepository,
) -> Optional[MessageTemplate]:
    return await respository.increase_usage_count(template_id=template_id)


async def send_media_group(
    message: Message,
    template: MessageTemplate,
    reply_message_id: Optional[int],
) -> None:
    """Отправляет медиа-группу"""
    try:

        media_group = []

        # Создаем медиа группу
        for i, media in enumerate(template.media_items):
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
            elif media.media_type == "document":
                media_group.append(
                    InputMediaDocument(
                        media=media.file_id,
                        caption=template.content if i == 0 else None,
                        parse_mode="HTML" if i == 0 else None,
                    )
                )

        if media_group:
            await message.bot.send_media_group(
                chat_id=message.chat.id,
                media=media_group,
                reply_to_message_id=reply_message_id,
            )
    except Exception:
        await message.bot.send_message(
            chat_id=message.chat.id,
            text=template.content,
            reply_to_message_id=reply_message_id,
            parse_mode="HTML",
        )


async def get_variants(query: str) -> List[MessageTemplate]:
    """Получает варианты шаблонов по запросу"""
    resp_repo: MessageTemplateRepository = container.resolve(MessageTemplateRepository)
    templates = await resp_repo.get_all_templates()

    # Сортируем шаблоны по количеству исользований
    sorted_templates = sorted(templates, key=lambda x: x.usage_count)

    return [
        template
        for template in sorted_templates
        if query.lower() in template.title.lower()
    ]


async def save_moderator_message(message: Message) -> None:
    """Сохраняет сообщение модератора в БД"""
    from .message_handler import group_message_handler

    await group_message_handler(message)
