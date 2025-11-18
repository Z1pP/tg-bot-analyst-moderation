import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from constants.callback import CallbackData
from constants.pagination import USERS_PAGE_SIZE
from container import container
from keyboards.inline.users import users_inline_kb, users_menu_ikb
from states import UserStateManager
from usecases.user_tracking import GetListTrackedUsersUseCase
from utils.exception_handler import handle_exception
from utils.state_logger import log_and_set_state

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data == CallbackData.User.SELECT_USER)
async def users_list_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик команды для отображения списка пользователей через inline клавиатуру"""
    await callback.answer()
    await state.clear()

    try:
        logger.info(
            f"Пользователь {callback.from_user.id} запросил список пользователей для отчета"
        )

        usecase: GetListTrackedUsersUseCase = container.resolve(
            GetListTrackedUsersUseCase
        )
        users = await usecase.execute(admin_tgid=str(callback.from_user.id))

        if not users:
            message_text = (
                "❗Чтобы получать отчёты по пользователям, "
                "необходимо добавить пользователя в отслеживаемые"
            )
            await callback.message.edit_text(
                text=message_text,
                reply_markup=users_menu_ikb(),
            )
            return

        logger.info(f"Найдено {len(users)} пользователей для отчета")

        # Показываем первую страницу
        first_page_users = users[:USERS_PAGE_SIZE]

        await callback.message.edit_text(
            text=f"Всего {len(users)} пользователей",
            reply_markup=users_inline_kb(
                users=first_page_users,
                page=1,
                total_count=len(users),
            ),
        )

        await log_and_set_state(
            message=callback.message,
            state=state,
            new_state=UserStateManager.listing_users,
        )
    except Exception as e:
        await handle_exception(callback.message, e, "users_list_handler")
