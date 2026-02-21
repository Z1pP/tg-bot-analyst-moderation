import logging

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from punq import Container

from constants import Dialog
from dto import UpdateTemplateTitleDTO
from exceptions.base import BotBaseException
from handlers._handler_errors import raise_business_logic
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
from states import TemplateStateManager
from usecases.templates import (
    GetTemplateByIdUseCase,
    UpdateTemplateContentUseCase,
    UpdateTemplateTitleUseCase,
)
from utils.send_message import safe_edit_message
from utils.template_content import extract_media_content_from_messages

from .common import validate_template_title

router = Router(name=__name__)
router.message.middleware(AlbumMiddleware())
logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith("edit_template__"))
async def edit_template_handler(
    callback: CallbackQuery, state: FSMContext, container: Container
) -> None:
    """Обработчик начала редактирования шаблона"""
    try:
        template_id = int(callback.data.split("__")[1])

        get_template_uc: GetTemplateByIdUseCase = container.resolve(
            GetTemplateByIdUseCase
        )
        template = await get_template_uc.execute(template_id)

        if not template:
            await callback.answer(
                Dialog.Template.TEMPLATE_NOT_FOUND_SHORT, show_alert=True
            )
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

        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Template.EDIT_TEMPLATE_TITLE.format(title=template.title),
            reply_markup=edit_template_kb(),
            parse_mode="HTML",
        )

        await state.set_state(TemplateStateManager.editing_template)

        logger.info(
            f"Начато редактирование шаблона {template_id} пользователем {callback.from_user.username}"
        )

    except BotBaseException as e:
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=e.get_user_message(),
            reply_markup=templates_menu_ikb(),
            parse_mode="HTML",
        )
    except Exception as e:
        raise_business_logic(
            "Ошибка в edit_template_callback.",
            Dialog.Template.ERROR_EDIT_TEMPLATE,
            e,
            logger,
        )
    finally:
        await callback.answer()


@router.callback_query(F.data == "edit_title", TemplateStateManager.editing_template)
async def edit_title_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик начала редактирования названия шаблона"""
    try:
        # Сохраняем message_id для последующего редактирования
        await state.update_data(active_message_id=callback.message.message_id)

        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Template.EDIT_TITLE_INPUT,
            reply_markup=cancel_edit_ikb(),
            parse_mode="HTML",
        )

        await state.set_state(TemplateStateManager.editing_title)

    except BotBaseException as e:
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=e.get_user_message(),
            reply_markup=cancel_edit_ikb(),
            parse_mode="HTML",
        )
    except Exception as e:
        raise_business_logic(
            "Ошибка в edit_title_callback.",
            Dialog.Template.ERROR_EDIT_TEMPLATE,
            e,
            logger,
        )
    finally:
        await callback.answer()


@router.message(TemplateStateManager.editing_title)
async def process_edit_title_handler(
    message: Message, state: FSMContext, bot: Bot, container: Container
) -> None:
    """Обработчик получения нового названия шаблона"""
    try:
        data = await state.get_data()
        template_id = data.get("edit_template_id")

        if not template_id:
            await message.reply(Dialog.Template.ERROR_TEMPLATE_NOT_FOUND)
            return

        new_title = message.text.strip()

        # Валидация названия
        if not validate_template_title(new_title):
            await message.reply(Dialog.Template.TITLE_VALIDATION_ERROR)
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
            await message.reply(Dialog.Template.ERROR_UPDATE_TITLE)
            return

        await message.delete()

        # Формируем сообщение об обновлении
        update_message = Dialog.Template.TITLE_UPDATED.format(
            old_title=old_title, new_title=new_title
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
                    data=state_data, page=1, container=container
                )
                await safe_edit_message(
                    bot=bot,
                    chat_id=message.chat.id,
                    message_id=active_message_id,
                    text=f"{update_message}\n\n{Dialog.Template.SELECT_TEMPLATE}",
                    reply_markup=templates_inline_kb(
                        templates=templates,
                        page=1,
                        total_count=total_count,
                        show_back_to_categories=True,
                    ),
                    parse_mode="HTML",
                )
                await state.set_state(TemplateStateManager.listing_templates)
            elif state_data.chat_id:
                templates, total_count = await get_templates_and_count(
                    data=state_data, page=1, container=container
                )
                await safe_edit_message(
                    bot=bot,
                    chat_id=message.chat.id,
                    message_id=active_message_id,
                    text=f"{update_message}\n\n{Dialog.Template.TEMPLATES_FOR_CHAT.format(count=total_count)}",
                    reply_markup=templates_inline_kb(
                        templates=templates,
                        page=1,
                        total_count=total_count,
                        show_back_to_categories=False,
                    ),
                    parse_mode="HTML",
                )
                await state.set_state(TemplateStateManager.listing_templates)
            elif state_data.template_scope == "global":
                templates, total_count = await get_templates_and_count(
                    data=state_data, page=1, container=container
                )
                await safe_edit_message(
                    bot=bot,
                    chat_id=message.chat.id,
                    message_id=active_message_id,
                    text=f"{update_message}\n\n{Dialog.Template.GLOBAL_TEMPLATES.format(count=total_count)}",
                    reply_markup=templates_inline_kb(
                        templates=templates,
                        page=1,
                        total_count=total_count,
                        show_back_to_categories=False,
                    ),
                    parse_mode="HTML",
                )
                await state.set_state(TemplateStateManager.listing_templates)
            else:
                await safe_edit_message(
                    bot=bot,
                    chat_id=message.chat.id,
                    message_id=active_message_id,
                    text=update_message,
                    reply_markup=templates_menu_ikb(),
                    parse_mode="HTML",
                )
                await state.set_state(TemplateStateManager.templates_menu)
        except Exception as e:
            raise_business_logic(
                "Ошибка при возврате к списку шаблонов (edit title).",
                Dialog.Template.ERROR_EDIT_TEMPLATE,
                e,
                logger,
            )

    except BotBaseException as e:
        await message.reply(e.get_user_message())
    except Exception as e:
        raise_business_logic(
            "Ошибка при обновлении названия шаблона.",
            Dialog.Template.ERROR_UPDATE_TITLE,
            e,
            logger,
        )


@router.callback_query(F.data == "edit_content", TemplateStateManager.editing_template)
async def edit_content_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик начала редактирования содержимого шаблона"""
    try:
        # Сохраняем message_id для последующего редактирования
        await state.update_data(active_message_id=callback.message.message_id)

        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Template.EDIT_CONTENT_INPUT,
            reply_markup=cancel_edit_ikb(),
            parse_mode="HTML",
        )

        await state.set_state(TemplateStateManager.editing_content)

    except BotBaseException as e:
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=e.get_user_message(),
            reply_markup=cancel_edit_ikb(),
            parse_mode="HTML",
        )
    except Exception as e:
        raise_business_logic(
            "Ошибка в edit_content_callback.",
            Dialog.Template.ERROR_EDIT_TEMPLATE,
            e,
            logger,
        )
    finally:
        await callback.answer()


@router.message(TemplateStateManager.editing_content)
async def process_edit_content_handler(
    message: Message,
    state: FSMContext,
    bot: Bot,
    container: Container,
    album_messages: list[Message] | None = None,
) -> None:
    """Обработчик получения нового содержимого шаблона"""
    try:
        data = await state.get_data()
        template_id = data.get("edit_template_id")

        if not template_id:
            await message.reply(Dialog.Template.ERROR_TEMPLATE_NOT_FOUND)
            return

        if album_messages:
            content_data = extract_media_content_from_messages(album_messages)
        else:
            content_data = extract_media_content_from_messages([message])

        update_content_uc: UpdateTemplateContentUseCase = container.resolve(
            UpdateTemplateContentUseCase
        )
        success = await update_content_uc.execute(
            template_id=template_id,
            content=content_data,
        )

        if not success:
            await message.reply(Dialog.Template.ERROR_UPDATE_CONTENT)
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
        update_message = Dialog.Template.CONTENT_UPDATED

        # Возвращаемся к списку шаблонов
        active_message_id = data.get("active_message_id")
        if not active_message_id:
            await message.reply(update_message)
            return

        try:
            state_data = await extract_state_data(state)

            if state_data.category_id:
                templates, total_count = await get_templates_and_count(
                    data=state_data, page=1, container=container
                )
                await safe_edit_message(
                    bot=bot,
                    chat_id=message.chat.id,
                    message_id=active_message_id,
                    text=f"{update_message}\n\n{Dialog.Template.SELECT_TEMPLATE}",
                    reply_markup=templates_inline_kb(
                        templates=templates,
                        page=1,
                        total_count=total_count,
                        show_back_to_categories=True,
                    ),
                )
                await state.set_state(TemplateStateManager.listing_templates)
            elif state_data.chat_id:
                templates, total_count = await get_templates_and_count(
                    data=state_data, page=1, container=container
                )
                await safe_edit_message(
                    bot=bot,
                    chat_id=message.chat.id,
                    message_id=active_message_id,
                    text=f"{update_message}\n\n{Dialog.Template.TEMPLATES_FOR_CHAT.format(count=total_count)}",
                    reply_markup=templates_inline_kb(
                        templates=templates,
                        page=1,
                        total_count=total_count,
                        show_back_to_categories=False,
                    ),
                )
                await state.set_state(TemplateStateManager.listing_templates)
            elif state_data.template_scope == "global":
                templates, total_count = await get_templates_and_count(
                    data=state_data, page=1, container=container
                )
                await safe_edit_message(
                    bot=bot,
                    chat_id=message.chat.id,
                    message_id=active_message_id,
                    text=f"{update_message}\n\n{Dialog.Template.GLOBAL_TEMPLATES.format(count=total_count)}",
                    reply_markup=templates_inline_kb(
                        templates=templates,
                        page=1,
                        total_count=total_count,
                        show_back_to_categories=False,
                    ),
                )
                await state.set_state(TemplateStateManager.listing_templates)
            else:
                await safe_edit_message(
                    bot=bot,
                    chat_id=message.chat.id,
                    message_id=active_message_id,
                    text=update_message,
                    reply_markup=templates_menu_ikb(),
                )
                await state.set_state(TemplateStateManager.templates_menu)
        except Exception as e:
            raise_business_logic(
                "Ошибка при возврате к списку шаблонов (edit content).",
                Dialog.Template.ERROR_EDIT_TEMPLATE,
                e,
                logger,
            )

    except BotBaseException as e:
        await message.reply(e.get_user_message())
    except Exception as e:
        raise_business_logic(
            "Ошибка при обновлении содержимого шаблона.",
            Dialog.Template.ERROR_UPDATE_CONTENT,
            e,
            logger,
        )


@router.callback_query(F.data == "cancel_edit", TemplateStateManager.editing_template)
async def cancel_edit_handler(
    callback: CallbackQuery, state: FSMContext, container: Container
) -> None:
    """Обработчик отмены редактирования"""
    try:
        await state.update_data(edit_template_id=None, original_title=None)

        # Возвращаемся к списку шаблонов
        try:
            state_data = await extract_state_data(state)

            if state_data.category_id:
                # Возвращаемся к списку шаблонов категории
                templates, total_count = await get_templates_and_count(
                    data=state_data, page=1, container=container
                )

                await safe_edit_message(
                    bot=callback.bot,
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    text=f"{Dialog.Template.EDIT_CANCELLED}\n\n{Dialog.Template.SELECT_TEMPLATE}",
                    reply_markup=templates_inline_kb(
                        templates=templates,
                        page=1,
                        total_count=total_count,
                        show_back_to_categories=True,
                    ),
                )
                await state.set_state(TemplateStateManager.listing_templates)
            elif state_data.chat_id:
                # Возвращаемся к списку шаблонов чата
                templates, total_count = await get_templates_and_count(
                    data=state_data, page=1, container=container
                )

                await safe_edit_message(
                    bot=callback.bot,
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    text=f"{Dialog.Template.EDIT_CANCELLED}\n\n{Dialog.Template.TEMPLATES_FOR_CHAT.format(count=total_count)}",
                    reply_markup=templates_inline_kb(
                        templates=templates,
                        page=1,
                        total_count=total_count,
                        show_back_to_categories=False,
                    ),
                )
                await state.set_state(TemplateStateManager.listing_templates)
            elif state_data.template_scope == "global":
                # Возвращаемся к списку глобальных шаблонов
                templates, total_count = await get_templates_and_count(
                    data=state_data, page=1, container=container
                )

                await safe_edit_message(
                    bot=callback.bot,
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    text=f"{Dialog.Template.EDIT_CANCELLED}\n\n{Dialog.Template.GLOBAL_TEMPLATES.format(count=total_count)}",
                    reply_markup=templates_inline_kb(
                        templates=templates,
                        page=1,
                        total_count=total_count,
                        show_back_to_categories=False,
                    ),
                )
                await state.set_state(TemplateStateManager.listing_templates)
            else:
                # Если нет ни category_id, ни chat_id, ни global scope, возвращаемся в меню
                await safe_edit_message(
                    bot=callback.bot,
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    text=Dialog.Template.EDIT_CANCELLED,
                    reply_markup=templates_menu_ikb(),
                )
                await state.set_state(TemplateStateManager.templates_menu)
        except Exception as e:
            raise_business_logic(
                "Ошибка при возврате к списку шаблонов (cancel_edit).",
                Dialog.Template.ERROR_EDIT_TEMPLATE,
                e,
                logger,
            )

    except BotBaseException as e:
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=e.get_user_message(),
            reply_markup=templates_menu_ikb(),
        )
    except Exception as e:
        raise_business_logic(
            "Ошибка в cancel_edit_callback.",
            Dialog.Template.ERROR_EDIT_TEMPLATE,
            e,
            logger,
        )
    finally:
        await callback.answer()


async def _cancel_edit_title_or_content(
    callback: CallbackQuery, state: FSMContext, container: Container
) -> None:
    """Вспомогательная функция для отмены редактирования названия или содержимого шаблона"""
    data = await state.get_data()
    template_id = data.get("edit_template_id")

    if not template_id:
        await callback.answer(Dialog.Template.ERROR_TEMPLATE_NOT_FOUND, show_alert=True)
        return

    get_template_uc: GetTemplateByIdUseCase = container.resolve(
        GetTemplateByIdUseCase
    )
    template = await get_template_uc.execute(template_id)

    if not template:
        await callback.answer(Dialog.Template.TEMPLATE_NOT_FOUND, show_alert=True)
        return

    # Возвращаемся к окну редактирования шаблона
    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Template.EDIT_TEMPLATE_TITLE.format(title=template.title),
        reply_markup=edit_template_kb(),
        parse_mode="HTML",
    )

    await state.set_state(TemplateStateManager.editing_template)

    logger.info(
        f"Отмена редактирования названия/содержимого шаблона {template_id}, "
        f"возврат к окну редактирования"
    )


@router.callback_query(
    F.data == "cancel_edit_title_or_content",
    TemplateStateManager.editing_title,
)
async def cancel_edit_title_handler(
    callback: CallbackQuery, state: FSMContext, container: Container
) -> None:
    """Обработчик отмены редактирования названия шаблона"""
    try:
        await _cancel_edit_title_or_content(callback, state, container)
    except BotBaseException as e:
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=e.get_user_message(),
            reply_markup=templates_menu_ikb(),
        )
    except Exception as e:
        raise_business_logic(
            "Ошибка в cancel_edit_title_callback.",
            Dialog.Template.ERROR_EDIT_TEMPLATE,
            e,
            logger,
        )
    finally:
        await callback.answer()


@router.callback_query(
    F.data == "cancel_edit_title_or_content",
    TemplateStateManager.editing_content,
)
async def cancel_edit_content_handler(
    callback: CallbackQuery, state: FSMContext, container: Container
) -> None:
    """Обработчик отмены редактирования содержимого шаблона"""
    try:
        await _cancel_edit_title_or_content(callback, state, container)
    except BotBaseException as e:
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=e.get_user_message(),
            reply_markup=templates_menu_ikb(),
        )
    except Exception as e:
        raise_business_logic(
            "Ошибка в cancel_edit_content_callback.",
            Dialog.Template.ERROR_EDIT_TEMPLATE,
            e,
            logger,
        )
    finally:
        await callback.answer()
