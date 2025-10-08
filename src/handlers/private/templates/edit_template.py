import logging
from typing import Any, Dict

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from container import container
from dto import UpdateTemplateTitleDTO
from middlewares import AlbumMiddleware
from services.templates import TemplateContentService
from states import TemplateStateManager
from usecases.templates import UpdateTemplateTitleUseCase
from utils.exception_handler import handle_exception

router = Router(name=__name__)
router.message.middleware(AlbumMiddleware())
logger = logging.getLogger(__name__)


@router.message(TemplateStateManager.editing_title)
async def process_edit_title(message: Message, state: FSMContext) -> None:
    """Обработчик изменения названия шаблона"""
    try:
        data = await state.get_data()
        template_id = data.get("edit_template_id")

        if not template_id:
            await message.answer("❌ Ошибка: шаблон не найден")
            await state.clear()
            return

        new_title = message.text.strip()

        # Обновляем название через Use Case
        usecase: UpdateTemplateTitleUseCase = container.resolve(
            UpdateTemplateTitleUseCase
        )
        update_dto = UpdateTemplateTitleDTO(
            template_id=template_id, new_title=new_title
        )
        success = await usecase.execute(update_dto)

        if success:
            await message.answer(f"✅ Название шаблона изменено на: <b>{new_title}</b>")
        else:
            await message.answer("❌ Ошибка при обновлении названия")

        await state.set_state(TemplateStateManager.templates_menu)
        await state.update_data(edit_template_id=None, original_title=None)

    except Exception as e:
        await handle_exception(message, e, "process_edit_title")
        await state.clear()


@router.message(TemplateStateManager.editing_content)
async def process_edit_content(
    message: Message,
    state: FSMContext,
    album_messages: list[Message] | None = None,
) -> None:
    """Обработчик изменения содержимого шаблона"""
    try:
        data = await state.get_data()
        template_id = data.get("edit_template_id")

        if not template_id:
            await message.answer("❌ Ошибка: шаблон не найден")
            await state.clear()
            return

        # Получаем сервис для обработки контента
        content_service: TemplateContentService = container.resolve(
            TemplateContentService
        )

        # Извлекаем новый контент
        content_data: Dict[str, Any] = dict()

        if album_messages:
            content_data = content_service.extract_media_content(
                messages=album_messages
            )
        else:
            content_data = content_service.extract_media_content(messages=[message])

        # Обновляем содержимое в БД через сервис
        success = await content_service.update_template_content(
            template_id, content_data
        )

        if success:
            await message.answer("✅ Содержимое шаблона успешно обновлено!")
            logger.info(f"Содержимое шаблона {template_id} обновлено")
        else:
            await message.answer("❌ Ошибка при обновлении содержимого")

        await state.set_state(TemplateStateManager.templates_menu)
        await state.update_data(edit_template_id=None, original_title=None)

    except Exception as e:
        await handle_exception(message, e, "process_edit_content")
        await state.clear()
