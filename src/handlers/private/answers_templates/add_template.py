import asyncio
import logging
import time
from typing import Any, Dict, Optional, Set

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from constants import KbCommands
from container import container
from keyboards.inline.categories import categories_inline_kb
from models import MessageTemplate
from repositories import (
    MessageTemplateRepository,
    TemplateCategoryRepository,
    TemplateMediaRepository,
    UserRepository,
)
from states import TemplateStateManager
from utils.send_message import send_html_message_with_kb

router = Router(name=__name__)
logger = logging.getLogger(__name__)

# Кеш для сбора медиагрупп
media_groups = {}
processed_media_groups: Set[str] = set()
processing_media_groups: Set[str] = set()


@router.message(F.text == KbCommands.ADD_TEMPLATE)
async def add_template_handler(message: Message, state: FSMContext):
    """Обработчик добавления нового шаблона"""
    try:
        category_repo: TemplateCategoryRepository = container.resolve(
            TemplateCategoryRepository
        )
        categories = await category_repo.get_all_categories()

        await send_html_message_with_kb(
            message=message,
            text="Пожалуйста, выберите категорию шаблона:",
            reply_markup=categories_inline_kb(categories=categories),
        )
        await state.set_state(TemplateStateManager.process_template_category)
    except Exception as e:
        logger.error(f"Ошибка при начале создания шаблона: {e}")
        await message.answer("Произошла ошибка при создании шаблона.")
        await state.clear()


@router.message(TemplateStateManager.process_template_title)
async def process_template_title_handler(message: Message, state: FSMContext):
    """Обработчик получения названия нового шаблона"""
    try:
        await state.update_data(title=message.text)
        await send_html_message_with_kb(
            message=message,
            text=f"Отправьте контент для шаблона '{message.text}' (текст, фото или медиагруппу):",
        )
        await state.set_state(TemplateStateManager.process_template_content)
    except Exception as e:
        logger.error(f"Ошибка при получении названия шаблона: {e}")
        await message.answer("Произошла ошибка при создании шаблона.")
        await state.clear()


@router.message(TemplateStateManager.process_template_content)
async def process_template_content_handler(message: Message, state: FSMContext):
    """Обработчик получения контента шаблона"""
    state_data = await state.get_data()
    title = state_data.get("title")

    try:
        content_data = extract_message_content(message)
        content_data.update(state_data)

        if content_data["media_group_id"]:
            await handle_media_group_message(message, state, content_data)
        else:
            await save_template(message.from_user.username, content_data)
            await message.answer(f"✅ Шаблон '{title}' создан!")
            await state.set_state(TemplateStateManager.templates_menu)

    except Exception as e:
        logger.error(f"Ошибка при создании шаблона: {e}", exc_info=True)
        await message.reply(f"❌ Ошибка при создании шаблона: {str(e)}")
        await state.clear()


async def handle_media_group_message(
    message: Message, state: FSMContext, content_data: Dict[str, Any]
):
    """Обрабатывает сообщение из медиагруппы"""
    group_id = content_data["media_group_id"]

    if group_id in processed_media_groups:
        return

    if group_id in processing_media_groups:
        if content_data["media_files"] and group_id in media_groups:
            media_groups[group_id]["files"].extend(content_data["media_files"])
            media_groups[group_id]["unique_ids"].extend(
                content_data["media_unique_ids"]
            )
        return

    processing_media_groups.add(group_id)
    await handle_media_group(message, state, content_data)


def extract_message_content(message: Message) -> Dict[str, Any]:
    """Извлекает контент из сообщения"""
    content = {
        "text": message.html_text or message.caption or "",
        "media_type": None,
        "media_files": [],
        "media_unique_ids": [],
        "media_group_id": message.media_group_id,
        "author": message.from_user.username,
    }

    media_mapping = {
        "photo": (message.photo, lambda x: x[-1]),
        "document": (message.document, lambda x: x),
        "video": (message.video, lambda x: x),
        "animation": (message.animation, lambda x: x),
    }

    for media_type, (media_obj, accessor) in media_mapping.items():
        if media_obj:
            media = accessor(media_obj)
            content.update(
                {
                    "media_type": media_type,
                    "media_files": [media.file_id],
                    "media_unique_ids": [media.file_unique_id],
                }
            )
            break

    return content


async def handle_media_group(
    message: Message, state: FSMContext, content_data: Dict[str, Any]
):
    """Обрабатывает медиагруппу"""
    group_id = content_data["media_group_id"]
    title = content_data["title"]

    try:
        if group_id not in media_groups:
            media_groups[group_id] = {
                "files": [],
                "unique_ids": [],
                "text": content_data["text"],
                "expires_at": time.time() + 60,
                "category_id": content_data["category_id"],
                "title": title,
            }

        if content_data["media_files"]:
            media_groups[group_id]["files"].extend(content_data["media_files"])
            media_groups[group_id]["unique_ids"].extend(
                content_data["media_unique_ids"]
            )

        await asyncio.sleep(3)

        group_data = media_groups.get(group_id)
        if group_data and group_data["files"]:
            full_content = {
                "text": group_data["text"],
                "media_type": content_data["media_type"],
                "media_files": group_data["files"],
                "media_unique_ids": group_data["unique_ids"],
                "media_group_id": group_id,
                "category_id": group_data["category_id"],
                "author": message.from_user.username,
                "title": title,
            }

            processed_media_groups.add(group_id)
            await save_template(message.from_user.username, full_content)
            await message.reply(f"✅ Шаблон '{title}' создан!")
            await state.set_state(TemplateStateManager.templates_menu)

            del media_groups[group_id]
            asyncio.create_task(clear_processed_group(group_id))
    finally:
        processing_media_groups.discard(group_id)


async def clear_processed_group(group_id: str, delay: int = 60):
    """Очищает обработанную группу через указанное время"""
    await asyncio.sleep(delay)
    processed_media_groups.discard(group_id)


async def save_template(
    author_username: str, content: Dict[str, Any]
) -> Optional[MessageTemplate]:
    """Сохраняет шаблон в базу данных"""
    try:
        user_repo: UserRepository = container.resolve(UserRepository)
        template_repo: MessageTemplateRepository = container.resolve(
            MessageTemplateRepository
        )

        user = await user_repo.get_user_by_username(username=author_username)
        if not user:
            raise ValueError("User not found")

        new_template = await template_repo.create_template(
            title=content.get("title", "Без названия"),
            content=content.get("text", ""),
            category_id=content.get("category_id"),
            author_id=user.id,
            chat_id=content.get("chat_id"),
        )

        await save_media_files(new_template.id, content)
        return new_template
    except Exception as e:
        logger.error(f"Ошибка сохранения шаблона: {e}", exc_info=True)
        raise


async def save_media_files(template_id: int, content: Dict[str, Any]) -> None:
    """Сохраняет медиа файлы в БД"""
    media_files = content.get("media_files", [])
    media_unique_ids = content.get("media_unique_ids", [])
    media_type = content.get("media_type")

    if not media_files or not media_type:
        return

    media_repo: TemplateMediaRepository = container.resolve(TemplateMediaRepository)

    for position, (file_id, file_unique_id) in enumerate(
        zip(media_files, media_unique_ids)
    ):
        try:
            await media_repo.create_media(
                template_id=template_id,
                media_type=media_type,
                file_id=file_id,
                file_unique_id=file_unique_id,
                position=position,
            )
        except Exception as e:
            logger.error(f"Ошибка сохранения медиа {file_id}: {e}", exc_info=True)
