from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from punq import Container

from constants.callback import CallbackData
from keyboards.inline.users import users_menu_ikb
from states import UserStateManager
from usecases.user_tracking import HasTrackedUsersUseCase

router = Router(name=__name__)


@router.callback_query(F.data == CallbackData.User.SELECT_USER)
async def back_to_users_menu_handler(
    callback: types.CallbackQuery, state: FSMContext, container: Container
):
    await callback.answer()

    usecase: HasTrackedUsersUseCase = container.resolve(HasTrackedUsersUseCase)
    has_tracked_users = await usecase.execute(admin_tgid=str(callback.from_user.id))

    await callback.message.edit_text(
        text="Выбери действие:",
        reply_markup=users_menu_ikb(has_tracked_users=has_tracked_users),
    )

    await state.set_state(UserStateManager.users_menu)
