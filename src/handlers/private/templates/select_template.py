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

from constants import Dialog
from container import container
from keyboards.inline.message_actions import hide_album_ikb, hide_template_ikb
from models import MessageTemplate, TemplateMedia
from repositories import MessageTemplateRepository
from states import TemplateStateManager
from utils.send_message import safe_edit_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(
    TemplateStateManager.listing_templates,
    F.data.startswith("template__"),
)
async def select_template_handler(
    query: CallbackQuery,
    bot: Bot,
    state: FSMContext,
) -> None:
    """Обработчик выбора шаблона"""
    template_id = query.data.split("__")[1]

    logger.info(
        f"Был выбран шаблон c ID={template_id} пользователем - {query.from_user.username}"
    )

    await send_template_handler(
        bot=bot,
        message=query.message,
        template_id=int(template_id),
    )

    await query.answer()


async def send_template_handler(
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
        await message.reply(Dialog.Template.TEMPLATE_NOT_FOUND)
        return

    media_items = template.media_items

    # Отправляем в зависимости от типа контента
    if not media_items:
        # Только текст
        sent_message = await bot.send_message(
            chat_id=message.chat.id,
            text=template.content,
            parse_mode="HTML",
            reply_markup=hide_template_ikb(0),  # Временно 0, обновим после отправки
        )
        # Обновляем клавиатуру с правильным message_id
        await bot.edit_message_reply_markup(
            chat_id=message.chat.id,
            message_id=sent_message.message_id,
            reply_markup=hide_template_ikb(sent_message.message_id),
        )
    elif len(media_items) == 1:
        # Одно фото с текстом
        await send_single_media(bot, message, template, media_items[0])
    else:
        # Группа медиа
        sent_messages = await send_media_group(bot, message, template, media_items)
        # Отправляем сообщение с кнопкой для скрытия альбома
        if sent_messages:
            message_ids = [msg.message_id for msg in sent_messages]
            await bot.send_message(
                chat_id=message.chat.id,
                text=Dialog.Template.HIDE_ALBUM,
                reply_markup=hide_album_ikb(message_ids),
            )


async def send_single_media(
    bot: Bot,
    message: Message,
    template: MessageTemplate,
    media: TemplateMedia,
) -> None:
    """Отправляет одиночный медиа файл с текстом"""

    try:
        if media.media_type == "photo":
            sent_message = await bot.send_photo(
                chat_id=message.chat.id,
                photo=media.file_id,
                caption=template.content,
                parse_mode="HTML",
                reply_markup=hide_template_ikb(0),  # Временно 0, обновим после отправки
            )
        elif media.media_type == "document":
            sent_message = await bot.send_document(
                chat_id=message.chat.id,
                document=media.file_id,
                caption=template.content,
                parse_mode="HTML",
                reply_markup=hide_template_ikb(0),
            )
        elif media.media_type == "video":
            sent_message = await bot.send_video(
                chat_id=message.chat.id,
                video=media.file_id,
                caption=template.content,
                parse_mode="HTML",
                reply_markup=hide_template_ikb(0),
            )
        elif media.media_type == "animation":
            sent_message = await bot.send_animation(
                chat_id=message.chat.id,
                animation=media.file_id,
                caption=template.content,
                parse_mode="HTML",
                reply_markup=hide_template_ikb(0),
            )
        else:
            return

        # Обновляем клавиатуру с правильным message_id
        await bot.edit_message_reply_markup(
            chat_id=message.chat.id,
            message_id=sent_message.message_id,
            reply_markup=hide_template_ikb(sent_message.message_id),
        )
    except Exception as e:
        logger.error(f"Ошибка при отправке шаблона: {e}")
        sent_message = await bot.send_message(
            chat_id=message.chat.id,
            text=f"❌ Медиа недоступно. Текст шаблона:\n\n{template.content}",
            parse_mode="HTML",
            reply_markup=hide_template_ikb(0),
        )
        await bot.edit_message_reply_markup(
            chat_id=message.chat.id,
            message_id=sent_message.message_id,
            reply_markup=hide_template_ikb(sent_message.message_id),
        )


async def send_media_group(
    bot: Bot,
    message: Message,
    template: MessageTemplate,
    media_files: List[TemplateMedia],
) -> list[Message]:
    """Отправляет группу медиа файлов и возвращает список отправленных сообщений"""
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
            sent_messages = await bot.send_media_group(
                chat_id=message.chat.id,
                media=media_group,
            )
            return sent_messages
        except Exception as e:
            logger.error(f"Ошибка при отправке медиа-группы: {e}")
            sent_message = await bot.send_message(
                chat_id=message.chat.id,
                text=Dialog.Template.MEDIA_UNAVAILABLE.format(content=template.content),
                parse_mode="HTML",
            )
            return [sent_message]
    return []


@router.callback_query(F.data.startswith("hide_template_"))
async def hide_template_handler(callback: CallbackQuery) -> None:
    """Обработчик скрытия шаблона (одно сообщение)"""
    try:
        message_id = int(callback.data.split("_")[2])
        await callback.bot.delete_message(
            chat_id=callback.message.chat.id,
            message_id=message_id,
        )
        # Удаляем само сообщение с кнопкой, если оно существует
        if callback.message:
            try:
                await callback.message.delete()
            except Exception:
                pass
        await callback.answer(Dialog.Template.MESSAGE_HIDDEN)
    except Exception as e:
        logger.error(f"Ошибка при скрытии шаблона: {e}")
        # Пытаемся отредактировать сообщение с ошибкой
        if callback.message:
            success = await safe_edit_message(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=Dialog.Template.ERROR_HIDE_MESSAGE,
            )
            if not success:
                # Если не удалось отредактировать, показываем alert
                await callback.answer(
                    Dialog.Template.ERROR_HIDE_MESSAGE, show_alert=True
                )
        else:
            await callback.answer(Dialog.Template.ERROR_HIDE_MESSAGE, show_alert=True)


@router.callback_query(F.data.startswith("hide_album_"))
async def hide_album_handler(callback: CallbackQuery) -> None:
    """Обработчик скрытия альбома шаблонов (несколько сообщений)"""
    try:
        # Извлекаем ID сообщений из callback_data
        message_ids_str = callback.data.replace("hide_album_", "")
        message_ids = [int(msg_id) for msg_id in message_ids_str.split(",") if msg_id]

        # Удаляем все сообщения альбома
        for msg_id in message_ids:
            try:
                await callback.bot.delete_message(
                    chat_id=callback.message.chat.id,
                    message_id=msg_id,
                )
            except Exception as e:
                logger.warning(f"Не удалось удалить сообщение {msg_id}: {e}")

        # Удаляем само сообщение с кнопкой
        if callback.message:
            try:
                await callback.message.delete()
            except Exception:
                pass

        await callback.answer(Dialog.Template.ALBUM_HIDDEN)
    except Exception as e:
        logger.error(f"Ошибка при скрытии альбома: {e}")
        # Пытаемся отредактировать сообщение с ошибкой
        if callback.message:
            success = await safe_edit_message(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=Dialog.Template.ERROR_HIDE_ALBUM,
            )
            if not success:
                # Если не удалось отредактировать, показываем alert
                await callback.answer(Dialog.Template.ERROR_HIDE_ALBUM, show_alert=True)
        else:
            await callback.answer(Dialog.Template.ERROR_HIDE_ALBUM, show_alert=True)
