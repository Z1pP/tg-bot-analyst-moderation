import asyncio
import logging
import time
from typing import Any, Dict, Optional, Set

from aiogram import Bot, F, Router
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
from states import QuickResponseStateManager
from utils.send_message import send_html_message_with_kb

router = Router(name=__name__)
logger = logging.getLogger(__name__)

# Кеш для сбора медиагрупп
media_groups = {}
# Множество для отслеживания обработанных групп
processed_media_groups: Set[str] = set()
# Множество для отслеживания обрабатываемых групп
processing_media_groups: Set[str] = set()


@router.message(F.text == KbCommands.ADD_TEMPLATE)
async def add_template_handler(message: Message, state: FSMContext):
    """Обработчик добавления нового шаблона"""
    category_repo = container.resolve(TemplateCategoryRepository)
    categories = await category_repo.get_all_categories()

    await send_html_message_with_kb(
        message=message,
        text="Пожалуйста, выберите категорию шаблона:",
        reply_markup=categories_inline_kb(categories=categories),
    )

    await state.set_state(QuickResponseStateManager.process_template_category)


@router.message(QuickResponseStateManager.process_template_title)
async def process_template_title_handler(message: Message, state: FSMContext):
    """Обработчик получения названия нового шаблона"""
    title = message.text
    await state.update_data(title=title)

    await send_html_message_with_kb(
        message=message,
        text=f"Отправьте контент для шаблона '{title}' (текст, фото или медиагруппу):",
    )

    await state.set_state(QuickResponseStateManager.process_template_content)


@router.message(QuickResponseStateManager.process_template_content)
async def process_template_content_handler(
    message: Message,
    bot: Bot,
    state: FSMContext,
):
    """Обработчик получения контента шаблона"""
    state_data = await state.get_data()
    title = state_data.get("title")
    category_id = state_data.get("category_id")

    try:
        # Извлекаем контент из сообщения
        content_data = extract_message_content(message)
        content_data["category_id"] = int(category_id)
        content_data["title"] = title

        # Обрабатываем медиагруппу или одиночное сообщение
        if content_data["media_group_id"]:
            group_id = content_data["media_group_id"]

            # Проверяем, не обрабатывается ли уже эта группа
            if group_id in processed_media_groups:
                return

            # Проверяем, не находится ли группа в процессе обработки
            if group_id in processing_media_groups:
                # Просто добавляем файл в группу и выходим
                if content_data["media_files"] and group_id in media_groups:
                    media_groups[group_id]["files"].extend(content_data["media_files"])
                return

            # Помечаем группу как обрабатываемую
            processing_media_groups.add(group_id)

            # Обрабатываем медиагруппу
            await handle_media_group(message, bot, state, content_data)
        else:
            # Обычное сообщение без медиагруппы
            await save_template(message.from_user.username, content_data, bot)

            await message.answer(f"✅ Шаблон '{title}' создан!")

        await state.set_state(QuickResponseStateManager.templates_menu)
    except Exception as e:
        logger.error(f"Error creating template: {str(e)}", exc_info=True)
        await message.reply(f"❌ Ошибка при создании шаблона: {str(e)}")
        await state.clear()


def extract_message_content(message: Message) -> Dict[str, Any]:
    """Извлекает контент из сообщения"""
    content = {
        "text": message.html_text or message.caption or "",
        "media_type": None,
        "media_files": [],
        "media_group_id": message.media_group_id,
        "author": message.from_user.username,
    }

    if message.photo:
        content["media_type"] = "photo"
        content["media_files"] = [message.photo[-1].file_id]
    elif message.document:
        content["media_type"] = "document"
        content["media_files"] = [message.document.file_id]

    return content


async def handle_media_group(
    message: Message,
    bot: Bot,
    state: FSMContext,
    content_data: Dict[str, Any],
    status_message: Message = None,
):
    """Обрабатывает медиагруппу"""
    group_id = content_data["media_group_id"]
    title = content_data["title"]

    try:
        # Инициализируем группу если первое сообщение
        if group_id not in media_groups:
            media_groups[group_id] = {
                "files": [],
                "text": content_data["text"],
                "expires_at": time.time() + 60,
                "category_id": content_data["category_id"],
                "title": title,
            }

        # Добавляем файл в группу
        if content_data["media_files"]:
            media_groups[group_id]["files"].extend(content_data["media_files"])

        # Ждем немного для сбора всех медиа
        await asyncio.sleep(3)  # Увеличиваем задержку для сбора всех фото

        # Проверяем, все ли медиа собраны
        group_data = media_groups.get(group_id)
        if group_data and len(group_data["files"]) > 0:
            # Создаем полный контент
            full_content = {
                "text": group_data["text"],
                "media_type": content_data["media_type"],
                "media_files": group_data["files"],
                "media_group_id": group_id,
                "category_id": group_data["category_id"],
                "author": message.from_user.username,
                "title": title,
            }

            # Помечаем группу как обработанную
            processed_media_groups.add(group_id)

            # Сохраняем шаблон
            await save_template(message.from_user.username, full_content, bot)

            # Удаляем статусное сообщение если оно есть
            if status_message:
                try:
                    await status_message.delete()
                except Exception:
                    pass

            await message.reply(f"✅ Шаблон '{title}' создан!")
            await state.set_state(QuickResponseStateManager.templates_menu)

            # Очищаем кеш
            if group_id in media_groups:
                del media_groups[group_id]

            # Запускаем очистку processed_groups через 60 секунд
            asyncio.create_task(clear_processed_group(group_id))
    finally:
        # Убираем группу из обрабатываемых
        if group_id in processing_media_groups:
            processing_media_groups.remove(group_id)


async def clear_processed_group(group_id: str, delay: int = 60):
    """Очищает обработанную группу через указанное время"""
    await asyncio.sleep(delay)
    if group_id in processed_media_groups:
        processed_media_groups.remove(group_id)


async def save_template(
    author_username: str,
    content: Dict[str, Any],
    bot: Bot,
) -> Optional[MessageTemplate]:
    """Сохраняет шаблон в базу данных"""
    try:
        # Получаем репозитории
        user_repo: UserRepository = container.resolve(UserRepository)
        response_repo: MessageTemplateRepository = container.resolve(
            MessageTemplateRepository
        )
        category_repo: TemplateCategoryRepository = container.resolve(
            TemplateCategoryRepository
        )

        # Получаем пользователя и категорию
        user: UserRepository = await user_repo.get_user_by_username(author_username)
        category: TemplateCategoryRepository = await category_repo.get_category_by_id(
            content.get("category_id")
        )

        if not user or not category:
            raise ValueError("User or category not found")

        # Создаем шаблон
        new_template = await response_repo.create_template(
            title=content.get("title", "Без названия"),
            content=content.get("text", ""),
            category_id=category.id,
            author_id=user.id,
        )

        # Сохраняем медиа если есть
        await save_media_files(new_template.id, content, bot)

        return new_template
    except Exception as e:
        logger.error(f"Error saving template: {str(e)}", exc_info=True)
        raise


async def save_media_files(
    template_id: int,
    content: Dict[str, Any],
    bot: Bot,
) -> None:
    """Сохраняет медиа файлы в БД используя file_id и file_unique_id"""
    media_files = content.get("media_files", [])
    media_type = content.get("media_type")

    if not media_files or not media_type:
        return

    media_repo: TemplateMediaRepository = container.resolve(TemplateMediaRepository)

    for position, file_id in enumerate(media_files):
        try:
            # Получаем информацию о файле
            file_info = await bot.get_file(file_id)

            # Сохраняем запись в БД с обоими ID
            await media_repo.create_media(
                template_id=template_id,
                media_type=media_type,
                file_id=file_id,
                file_unique_id=file_info.file_unique_id,
                position=position,
            )
        except Exception as e:
            logger.error(f"Error saving media {file_id}: {str(e)}", exc_info=True)
