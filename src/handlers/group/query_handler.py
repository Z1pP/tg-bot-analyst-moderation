import logging
import re
from typing import List, Optional

from aiogram import F, Router
from aiogram.types import (
    CallbackQuery,
    InlineQuery,
    InlineQueryResultArticle,
    InlineQueryResultUnion,
    InputMediaAnimation,
    InputMediaDocument,
    InputMediaPhoto,
    InputMediaVideo,
    InputTextMessageContent,
    Message,
)
from punq import Container

from dto import TemplateDTO
from filters import StaffOnlyInlineFilter
from models import MessageTemplate
from usecases.templates import (
    GetTemplateAndIncreaseUsageUseCase,
    GetTemplatesByQueryUseCase,
)
from utils.send_message import safe_edit_callback_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.inline_query(
    F.query,
    StaffOnlyInlineFilter(),
)
async def handle_inline_query(query: InlineQuery, container: Container) -> None:
    """Обработчик inline запросов"""
    try:
        variants = await get_variants(query.query, container)
        results: list[InlineQueryResultUnion] = []

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
async def handle_template_message(message: Message, container: Container) -> None:
    """Обработчик сообщений с маркером шаблона"""
    if message.text is None:
        return
    try:
        # Извлекаем ID шаблона
        template_id = int(message.text.replace("🔸TEMPLATE__", ""))
        chat_id = str(message.chat.id)

        reply_message_id = (
            message.reply_to_message.message_id if message.reply_to_message else None
        )

        # Сохраняем сообщение модератора
        await save_moderator_message(message, container)

        # Удаляем сообщение с маркером
        await message.delete()

        # Отправляем шаблон
        await send_template(
            message=message,
            template_id=template_id,
            reply_message_id=reply_message_id,
            chat_id=chat_id,
            container=container,
        )

    except Exception as e:
        logger.error(f"Ошибка при отправке шаблона сообщения: {e}")


async def send_template(
    message: Message,
    template_id: int,
    chat_id: str,
    reply_message_id: Optional[int],
    container: Container,
) -> None:
    """Отправляет ответ по шаблону"""
    bot = message.bot
    if bot is None:
        return
    usecase: GetTemplateAndIncreaseUsageUseCase = container.resolve(
        GetTemplateAndIncreaseUsageUseCase
    )

    template = await usecase.execute(
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
        await bot.send_message(
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
    bot = message.bot
    if bot is None:
        return
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
                await bot.get_file(file_id=media.file_id)

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
            await bot.send_media_group(
                chat_id=message.chat.id,
                media=media_group,
                reply_to_message_id=reply_message_id,
            )
        else:
            await bot.send_message(
                chat_id=message.chat.id,
                text=f"{template.content}\n\n⚠️ Медиафайлы временно недоступны",
                reply_to_message_id=reply_message_id,
                parse_mode="HTML",
            )
    except Exception as e:
        logger.error(f"Ошибка при отправке медиа-группы: {e}")
        # Отправляем только текст в случае ошибки
        await bot.send_message(
            chat_id=message.chat.id,
            text=template.content,
            reply_to_message_id=reply_message_id,
            parse_mode="HTML",
        )


async def get_variants(query: str, container: Container) -> List[TemplateDTO]:
    """Получает варианты шаблонов по запросу"""
    usecase: GetTemplatesByQueryUseCase = container.resolve(GetTemplatesByQueryUseCase)
    result = await usecase.execute(query=query)
    return result.templates


async def save_moderator_message(message: Message, container: Container) -> None:
    """Сохраняет сообщение модератора в БД"""
    from .new_message import group_message_handler

    await group_message_handler(message, container)


@router.callback_query(F.data.startswith("hide_template_"))
async def hide_template_handler(callback: CallbackQuery) -> None:
    """Обработчик скрытия шаблона (одно сообщение)"""
    if callback.data is None or callback.bot is None or callback.message is None:
        return
    bot = callback.bot
    try:
        message_id = int(callback.data.split("_")[2])
        await bot.delete_message(
            chat_id=callback.message.chat.id,
            message_id=message_id,
        )
        # Удаляем само сообщение с кнопкой, если оно существует
        if isinstance(callback.message, Message):
            try:
                await callback.message.delete()
            except Exception as e:
                logger.debug("Не удалось удалить сообщение: %s", e, exc_info=True)
        await callback.answer("✅ Сообщение скрыто")
    except Exception as e:
        logger.error(f"Ошибка при скрытии шаблона: {e}")
        # Пытаемся отредактировать сообщение с ошибкой
        if callback.message:
            success = await safe_edit_callback_message(
                callback=callback,
                text="❌ Ошибка при скрытии сообщения",
            )
            if not success:
                # Если не удалось отредактировать, показываем alert
                await callback.answer(
                    "❌ Ошибка при скрытии сообщения", show_alert=True
                )
        else:
            await callback.answer("❌ Ошибка при скрытии сообщения", show_alert=True)


@router.callback_query(F.data.startswith("hide_album_"))
async def hide_album_handler(callback: CallbackQuery) -> None:
    """Обработчик скрытия альбома шаблонов (несколько сообщений)"""
    if callback.data is None or callback.bot is None or callback.message is None:
        return
    bot = callback.bot
    try:
        # Извлекаем ID сообщений из callback_data
        message_ids_str = callback.data.replace("hide_album_", "")
        message_ids = [int(msg_id) for msg_id in message_ids_str.split(",") if msg_id]

        # Удаляем все сообщения альбома
        for msg_id in message_ids:
            try:
                await bot.delete_message(
                    chat_id=callback.message.chat.id,
                    message_id=msg_id,
                )
            except Exception as e:
                logger.warning(f"Не удалось удалить сообщение {msg_id}: {e}")

        # Удаляем само сообщение с кнопкой
        if isinstance(callback.message, Message):
            try:
                await callback.message.delete()
            except Exception as e:
                logger.debug("Не удалось удалить сообщение: %s", e, exc_info=True)

        await callback.answer("✅ Альбом скрыт")
    except Exception as e:
        logger.error(f"Ошибка при скрытии альбома: {e}")
        # Пытаемся отредактировать сообщение с ошибкой
        if callback.message:
            success = await safe_edit_callback_message(
                callback=callback,
                text="❌ Ошибка при скрытии альбома",
            )
            if not success:
                # Если не удалось отредактировать, показываем alert
                await callback.answer("❌ Ошибка при скрытии альбома", show_alert=True)
        else:
            await callback.answer("❌ Ошибка при скрытии альбома", show_alert=True)
