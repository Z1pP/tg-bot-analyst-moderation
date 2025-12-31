from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from container import container
from keyboards.inline.template_scope import template_scope_selection_ikb
from states import TemplateStateManager
from usecases.chat import GetTrackedChatsUseCase
from utils.exception_handler import handle_exception

router = Router(name=__name__)


@router.callback_query(F.data == "select_template")
async def templates_list_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
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

        await callback.message.edit_text(
            text="Для какого чата вы хотите получить шаблоны:",
            reply_markup=template_scope_selection_ikb(chats),
        )

        await state.set_state(TemplateStateManager.selecting_template_scope)

    except Exception as e:
        await handle_exception(
            message=callback,
            exc=e,
            context="templates_list_handler",
        )
