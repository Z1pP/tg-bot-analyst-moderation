import logging

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from container import container
from dto import UpdateTemplateTitleDTO
from handlers.private.templates.pagination import (
    extract_state_data,
    get_templates_and_count,
)
from keyboards.inline.templates import (
    cancel_edit_ikb,
    edit_template_kb,
    templates_inline_kb,
    templates_menu_ikb,
)
from middlewares import AlbumMiddleware
from repositories import MessageTemplateRepository
from services.templates import TemplateContentService
from states import TemplateStateManager
from usecases.templates import UpdateTemplateTitleUseCase
from utils.exception_handler import handle_exception
from utils.state_logger import log_and_set_state

from .common import validate_template_title

router = Router(name=__name__)
router.message.middleware(AlbumMiddleware())
logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith("edit_template__"))
async def edit_template_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик начала редактирования шаблона"""
    try:
        template_id = int(callback.data.split("__")[1])

        # Получаем шаблон из БД
        template_repo: MessageTemplateRepository = container.resolve(
            MessageTemplateRepository
        )
        template = await template_repo.get_template_by_id(template_id)

        if not template:
            await callback.answer("Шаблон не найден", show_alert=True)
            return

        # Сохраняем данные шаблона и текущие данные из state для возврата к списку
        current_data = await state.get_data()
        await state.update_data(
            edit_template_id=template_id,
            original_title=template.title,
            category_id=current_data.get("category_id"),
            chat_id=current_data.get("chat_id"),
            template_scope=current_data.get("template_scope"),
        )

        await callback.message.edit_text(
            text=f"<b>Редактирование шаблона:</b> {template.title}\n\n"
            "Что вы хотите изменить?",
            reply_markup=edit_template_kb(),
            parse_mode="HTML",
        )

        await log_and_set_state(
            message=callback.message,
            state=state,
            new_state=TemplateStateManager.editing_template,
        )

        logger.info(
            f"Начато редактирование шаблона {template_id} пользователем {callback.from_user.username}"
        )

    except Exception as e:
        await handle_exception(callback.message, e, "edit_template_callback")
    finally:
        await callback.answer()


@router.callback_query(F.data == "edit_title", TemplateStateManager.editing_template)
async def edit_title_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик начала редактирования названия шаблона"""
    try:
        # Сохраняем message_id для последующего редактирования
        await state.update_data(active_message_id=callback.message.message_id)

        await callback.message.edit_text(
            text="<b>Редактирование названия</b>\n\nОтправьте новое название шаблона:",
            reply_markup=cancel_edit_ikb(),
            parse_mode="HTML",
        )

        await log_and_set_state(
            message=callback.message,
            state=state,
            new_state=TemplateStateManager.editing_title,
        )

    except Exception as e:
        await handle_exception(callback.message, e, "edit_title_callback")
    finally:
        await callback.answer()


@router.message(TemplateStateManager.editing_title)
async def process_edit_title_handler(
    message: Message, state: FSMContext, bot: Bot
) -> None:
    """Обработчик получения нового названия шаблона"""
    try:
        data = await state.get_data()
        template_id = data.get("edit_template_id")

        if not template_id:
            await message.reply("❌ Ошибка: шаблон не найден")
            return

        new_title = message.text.strip()

        # Валидация названия
        if not validate_template_title(new_title):
            await message.reply("❗Название должно содержать от 3 до 50 символов.")
            return

        # Получаем старое название
        old_title = data.get("original_title", "неизвестно")

        # Обновляем название в БД
        usecase: UpdateTemplateTitleUseCase = container.resolve(
            UpdateTemplateTitleUseCase
        )
        update_dto = UpdateTemplateTitleDTO(
            template_id=template_id,
            new_title=new_title,
        )
        success = await usecase.execute(update_dto)

        if not success:
            await message.reply("❌ Ошибка при обновлении названия шаблона")
            return

        await message.delete()

        # Формируем сообщение об обновлении
        update_message = (
            f"✅ Название шаблона обновлено\n\n"
            f"<b>Было:</b> {old_title}\n"
            f"<b>Стало:</b> {new_title}"
        )

        # Возвращаемся к списку шаблонов
        active_message_id = data.get("active_message_id")
        if not active_message_id:
            await message.reply(update_message, parse_mode="HTML")
            return

        try:
            state_data = await extract_state_data(state)

            if state_data.category_id:
                templates, total_count = await get_templates_and_count(
                    data=state_data, page=1
                )
                await bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=active_message_id,
                    text=f"{update_message}\n\nВыберите шаблон:",
                    reply_markup=templates_inline_kb(
                        templates=templates,
                        page=1,
                        total_count=total_count,
                        show_back_to_categories=True,
                    ),
                    parse_mode="HTML",
                )
                await log_and_set_state(
                    message=message,
                    state=state,
                    new_state=TemplateStateManager.listing_templates,
                )
            elif state_data.chat_id:
                templates, total_count = await get_templates_and_count(
                    data=state_data, page=1
                )
                await bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=active_message_id,
                    text=f"{update_message}\n\nШаблоны для чата ({total_count}):",
                    reply_markup=templates_inline_kb(
                        templates=templates,
                        page=1,
                        total_count=total_count,
                        show_back_to_categories=False,
                    ),
                    parse_mode="HTML",
                )
                await log_and_set_state(
                    message=message,
                    state=state,
                    new_state=TemplateStateManager.listing_templates,
                )
            elif state_data.template_scope == "global":
                templates, total_count = await get_templates_and_count(
                    data=state_data, page=1
                )
                await bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=active_message_id,
                    text=f"{update_message}\n\nГлобальные шаблоны ({total_count}):",
                    reply_markup=templates_inline_kb(
                        templates=templates,
                        page=1,
                        total_count=total_count,
                        show_back_to_categories=False,
                    ),
                    parse_mode="HTML",
                )
                await log_and_set_state(
                    message=message,
                    state=state,
                    new_state=TemplateStateManager.listing_templates,
                )
            else:
                await bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=active_message_id,
                    text=update_message,
                    reply_markup=templates_menu_ikb(),
                    parse_mode="HTML",
                )
                await log_and_set_state(
                    message=message,
                    state=state,
                    new_state=TemplateStateManager.templates_menu,
                )
        except Exception as e:
            logger.error("Ошибка при возврате к списку шаблонов: %s", e, exc_info=True)
            await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=active_message_id,
                text=update_message,
                reply_markup=templates_menu_ikb(),
                parse_mode="HTML",
            )
            await log_and_set_state(
                message=message,
                state=state,
                new_state=TemplateStateManager.templates_menu,
            )

    except Exception as e:
        logger.error("Ошибка при обновлении названия шаблона: %s", e, exc_info=True)
        await message.reply("❌ Ошибка при обновлении названия шаблона")


@router.callback_query(F.data == "edit_content", TemplateStateManager.editing_template)
async def edit_content_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик начала редактирования содержимого шаблона"""
    try:
        # Сохраняем message_id для последующего редактирования
        await state.update_data(active_message_id=callback.message.message_id)

        await callback.message.edit_text(
            text="<b>Редактирование содержимого</b>\n\n"
            "Отправьте новое содержимое для шаблона или перешлите сообщение из чата "
            "(текст, фото или медиагруппу):",
            reply_markup=cancel_edit_ikb(),
            parse_mode="HTML",
        )

        await log_and_set_state(
            message=callback.message,
            state=state,
            new_state=TemplateStateManager.editing_content,
        )

    except Exception as e:
        await handle_exception(callback.message, e, "edit_content_callback")
    finally:
        await callback.answer()


@router.message(TemplateStateManager.editing_content)
async def process_edit_content_handler(
    message: Message,
    state: FSMContext,
    bot: Bot,
    album_messages: list[Message] | None = None,
) -> None:
    """Обработчик получения нового содержимого шаблона"""
    try:
        data = await state.get_data()
        template_id = data.get("edit_template_id")

        if not template_id:
            await message.reply("❌ Ошибка: шаблон не найден")
            return

        # Извлекаем контент из сообщения(ий)
        content_service: TemplateContentService = container.resolve(
            TemplateContentService
        )

        if album_messages:
            content_data = content_service.extract_media_content(
                messages=album_messages
            )
        else:
            content_data = content_service.extract_media_content(messages=[message])

        # Обновляем контент в БД
        success = await content_service.update_template_content(
            template_id=template_id,
            content=content_data,
        )

        if not success:
            await message.reply("❌ Ошибка при обновлении содержимого шаблона")
            return

        # Удаляем сообщение(я) - если медиагруппа, удаляем все сообщения
        if album_messages:
            for msg in album_messages:
                try:
                    await msg.delete()
                except Exception as e:
                    logger.warning(
                        f"Не удалось удалить сообщение {msg.message_id}: {e}"
                    )
        else:
            await message.delete()

        # Формируем сообщение об обновлении
        update_message = "✅ Содержимое шаблона обновлено"

        # Возвращаемся к списку шаблонов
        active_message_id = data.get("active_message_id")
        if not active_message_id:
            await message.reply(update_message)
            return

        try:
            state_data = await extract_state_data(state)

            if state_data.category_id:
                templates, total_count = await get_templates_and_count(
                    data=state_data, page=1
                )
                await bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=active_message_id,
                    text=f"{update_message}\n\nВыберите шаблон:",
                    reply_markup=templates_inline_kb(
                        templates=templates,
                        page=1,
                        total_count=total_count,
                        show_back_to_categories=True,
                    ),
                )
                await log_and_set_state(
                    message=message,
                    state=state,
                    new_state=TemplateStateManager.listing_templates,
                )
            elif state_data.chat_id:
                templates, total_count = await get_templates_and_count(
                    data=state_data, page=1
                )
                await bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=active_message_id,
                    text=f"{update_message}\n\nШаблоны для чата ({total_count}):",
                    reply_markup=templates_inline_kb(
                        templates=templates,
                        page=1,
                        total_count=total_count,
                        show_back_to_categories=False,
                    ),
                )
                await log_and_set_state(
                    message=message,
                    state=state,
                    new_state=TemplateStateManager.listing_templates,
                )
            elif state_data.template_scope == "global":
                templates, total_count = await get_templates_and_count(
                    data=state_data, page=1
                )
                await bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=active_message_id,
                    text=f"{update_message}\n\nГлобальные шаблоны ({total_count}):",
                    reply_markup=templates_inline_kb(
                        templates=templates,
                        page=1,
                        total_count=total_count,
                        show_back_to_categories=False,
                    ),
                )
                await log_and_set_state(
                    message=message,
                    state=state,
                    new_state=TemplateStateManager.listing_templates,
                )
            else:
                await bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=active_message_id,
                    text=update_message,
                    reply_markup=templates_menu_ikb(),
                )
                await log_and_set_state(
                    message=message,
                    state=state,
                    new_state=TemplateStateManager.templates_menu,
                )
        except Exception as e:
            logger.error("Ошибка при возврате к списку шаблонов: %s", e, exc_info=True)
            await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=active_message_id,
                text=update_message,
                reply_markup=templates_menu_ikb(),
            )
            await log_and_set_state(
                message=message,
                state=state,
                new_state=TemplateStateManager.templates_menu,
            )

    except Exception as e:
        logger.error("Ошибка при обновлении содержимого шаблона: %s", e, exc_info=True)
        await message.reply("❌ Ошибка при обновлении содержимого шаблона")


@router.callback_query(F.data == "cancel_edit", TemplateStateManager.editing_template)
async def cancel_edit_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик отмены редактирования"""
    try:
        await state.update_data(edit_template_id=None, original_title=None)

        # Возвращаемся к списку шаблонов
        try:
            state_data = await extract_state_data(state)

            if state_data.category_id:
                # Возвращаемся к списку шаблонов категории
                templates, total_count = await get_templates_and_count(
                    data=state_data, page=1
                )

                await callback.message.edit_text(
                    text="❌ Редактирование отменено\n\nВыберите шаблон:",
                    reply_markup=templates_inline_kb(
                        templates=templates,
                        page=1,
                        total_count=total_count,
                        show_back_to_categories=True,
                    ),
                )
                await log_and_set_state(
                    message=callback.message,
                    state=state,
                    new_state=TemplateStateManager.listing_templates,
                )
            elif state_data.chat_id:
                # Возвращаемся к списку шаблонов чата
                templates, total_count = await get_templates_and_count(
                    data=state_data, page=1
                )

                await callback.message.edit_text(
                    text=f"❌ Редактирование отменено\n\nШаблоны для чата ({total_count}):",
                    reply_markup=templates_inline_kb(
                        templates=templates,
                        page=1,
                        total_count=total_count,
                        show_back_to_categories=False,
                    ),
                )
                await log_and_set_state(
                    message=callback.message,
                    state=state,
                    new_state=TemplateStateManager.listing_templates,
                )
            elif state_data.template_scope == "global":
                # Возвращаемся к списку глобальных шаблонов
                templates, total_count = await get_templates_and_count(
                    data=state_data, page=1
                )

                await callback.message.edit_text(
                    text=f"❌ Редактирование отменено\n\nГлобальные шаблоны ({total_count}):",
                    reply_markup=templates_inline_kb(
                        templates=templates,
                        page=1,
                        total_count=total_count,
                        show_back_to_categories=False,
                    ),
                )
                await log_and_set_state(
                    message=callback.message,
                    state=state,
                    new_state=TemplateStateManager.listing_templates,
                )
            else:
                # Если нет ни category_id, ни chat_id, ни global scope, возвращаемся в меню
                await callback.message.edit_text(
                    text="❌ Редактирование отменено",
                    reply_markup=templates_menu_ikb(),
                )
                await log_and_set_state(
                    message=callback.message,
                    state=state,
                    new_state=TemplateStateManager.templates_menu,
                )
        except Exception as e:
            logger.error("Ошибка при возврате к списку шаблонов: %s", e, exc_info=True)
            await callback.message.edit_text(
                text="❌ Произошла ошибка при редактировнии шаблона.",
                reply_markup=templates_menu_ikb(),
            )
            await log_and_set_state(
                message=callback.message,
                state=state,
                new_state=TemplateStateManager.templates_menu,
            )

    except Exception as e:
        await handle_exception(callback.message, e, "cancel_edit_callback")
    finally:
        await callback.answer()


async def _cancel_edit_title_or_content(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Вспомогательная функция для отмены редактирования названия или содержимого шаблона"""
    data = await state.get_data()
    template_id = data.get("edit_template_id")

    if not template_id:
        await callback.answer("❌ Ошибка: шаблон не найден", show_alert=True)
        return

    # Получаем шаблон из БД
    template_repo: MessageTemplateRepository = container.resolve(
        MessageTemplateRepository
    )
    template = await template_repo.get_template_by_id(template_id)

    if not template:
        await callback.answer("❌ Шаблон не найден", show_alert=True)
        return

    # Возвращаемся к окну редактирования шаблона
    await callback.message.edit_text(
        text=f"<b>Редактирование шаблона:</b> {template.title}\n\n"
        "Что вы хотите изменить?",
        reply_markup=edit_template_kb(),
        parse_mode="HTML",
    )

    await log_and_set_state(
        message=callback.message,
        state=state,
        new_state=TemplateStateManager.editing_template,
    )

    logger.info(
        f"Отмена редактирования названия/содержимого шаблона {template_id}, "
        f"возврат к окну редактирования"
    )


@router.callback_query(
    F.data == "cancel_edit_title_or_content",
    TemplateStateManager.editing_title,
)
async def cancel_edit_title_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик отмены редактирования названия шаблона"""
    try:
        await _cancel_edit_title_or_content(callback, state)
    except Exception as e:
        await handle_exception(callback.message, e, "cancel_edit_title_callback")
    finally:
        await callback.answer()


@router.callback_query(
    F.data == "cancel_edit_title_or_content",
    TemplateStateManager.editing_content,
)
async def cancel_edit_content_handler(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Обработчик отмены редактирования содержимого шаблона"""
    try:
        await _cancel_edit_title_or_content(callback, state)
    except Exception as e:
        await handle_exception(callback.message, e, "cancel_edit_content_callback")
    finally:
        await callback.answer()
