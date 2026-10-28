import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from punq import Container

from exceptions.base import BotBaseException
from keyboards.inline.templates import templates_menu_ikb
from keyboards.inline.template_scope import template_scope_selection_ikb
from states import TemplateStateManager
from usecases.chat import GetTrackedChatsUseCase
from utils.send_message import safe_edit_callback_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "select_template")
async def templates_list_handler(
    callback: types.CallbackQuery, state: FSMContext, container: Container
) -> None:
    """
    Обработчик команды для выбора области шаблонов.
    """
    await callback.answer()
    await state.clear()

    try:
        # Получаем список чатов пользователя
        usecase: GetTrackedChatsUseCase = container.resolve(GetTrackedChatsUseCase)
        chats = await usecase.execute(tg_id=str(callback.from_user.id))

        await safe_edit_callback_message(
            callback=callback,
            text="Для какого чата вы хотите получить шаблоны:",
            reply_markup=template_scope_selection_ikb(chats),
        )

        await state.set_state(TemplateStateManager.selecting_template_scope)

    except BotBaseException as e:
        await safe_edit_callback_message(
            callback=callback,
            text=e.get_user_message(),
            reply_markup=templates_menu_ikb(),
        )
    except Exception as e:
        logger.error("Ошибка в templates_list_handler: %s", e, exc_info=True)
        await safe_edit_callback_message(
            callback=callback,
            text="❌ Произошла непредвиденная ошибка. Попробуйте позже.",
            reply_markup=templates_menu_ikb(),
        )