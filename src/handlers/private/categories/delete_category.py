import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from container import container
from exceptions.category import CategoryNotFoundError
from keyboards.inline.categories import conf_remove_category_kb
from keyboards.inline.templates import templates_menu_ikb
from states import CategoryStateManager, TemplateStateManager
from usecases.categories import DeleteCategoryUseCase
from utils.send_message import safe_edit_message
from utils.state_logger import log_and_set_state

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(
    F.data.startswith("remove_category__"),
    TemplateStateManager.listing_categories,
)
async def remove_category_handler(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработчик запроса на удаление категории"""
    await callback.answer()

    try:
        category_id = int(callback.data.split("__")[1])
    except (IndexError, ValueError):
        logger.warning("Некорректный формат callback_data: %s", callback.data)
        return

    logger.info(
        "Пользователь '%s' инициировал удаление категории ID=%d",
        callback.from_user.full_name,
        category_id,
    )

    await state.update_data(category_id=category_id)

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text="Вы уверены, что хотите удалить эту категорию?",
        reply_markup=conf_remove_category_kb(),
    )

    await log_and_set_state(
        message=callback.message,
        state=state,
        new_state=CategoryStateManager.removing_category,
    )


@router.callback_query(
    F.data == "conf_remove_category",
    CategoryStateManager.removing_category,
)
async def confirm_removing_category_handler(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработчик подтверждения удаления категории"""
    await callback.answer()

    data = await state.get_data()
    category_id = data.get("category_id")

    if not category_id:
        logger.warning("Попытка удалить категорию без сохранённого ID в состоянии")
        return await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text="⚠️ Не удалось определить категорию для удаления.",
            reply_markup=templates_menu_ikb(),
        )

    try:
        usecase: DeleteCategoryUseCase = container.resolve(DeleteCategoryUseCase)
        category = await usecase.execute(category_id=category_id)
        text = (
            f"✅ Категория <b>{category.name}</b> успешно удалена.\n"
            "Вы всегда можете создать её снова при необходимости."
        )
        logger.info("Категория ID=%d успешно удалена", category_id)

    except CategoryNotFoundError as e:
        logger.warning("Категория ID=%d не найдена: %s", category_id, e)
        text = e.get_user_message()

    except Exception:
        logger.exception("Ошибка при удалении категории ID=%d", category_id)
        text = "⚠️ Произошла ошибка при удалении категории."

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=text,
        reply_markup=templates_menu_ikb(),
    )

    await log_and_set_state(
        message=callback.message,
        state=state,
        new_state=TemplateStateManager.templates_menu,
    )


@router.callback_query(
    F.data == "cancel_remove_category",
    CategoryStateManager.removing_category,
)
async def cancel_removing_category_handler(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработчик отмены удаления категории"""
    await callback.answer()

    logger.info(
        "Пользователь '%s' отменил удаление категории", callback.from_user.full_name
    )

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text="❌ Удаление категории отменено.",
        reply_markup=templates_menu_ikb(),
    )

    await log_and_set_state(
        message=callback.message,
        state=state,
        new_state=TemplateStateManager.templates_menu,
    )
