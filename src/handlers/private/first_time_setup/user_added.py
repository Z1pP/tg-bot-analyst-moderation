import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from punq import Container

from constants import Dialog
from dto import UserTrackingDTO
from keyboards.inline.users import move_to_analytics_ikb
from states.first_time_setup import FirstTimeSetupStates
from usecases.chat_tracking import GetUserTrackedChatsUseCase
from usecases.user_tracking import AddUserToTrackingUseCase
from utils.user_data_parser import parse_data_from_text

from .helpers import _show_error_and_stay, _show_time_menu

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.message(FirstTimeSetupStates.waiting_user_added, F.text)
async def process_user_added(
    message: Message,
    state: FSMContext,
    container: Container,
) -> None:
    """
    Обработчик нажатия на кнопку продолжить настройку после добавления пользователя
    (начать настройку времени начала работы или вернуться в меню настроек пользователей и чатов).
    """

    data = await state.get_data()
    active_message_id = data.get("active_message_id")

    admin_id = message.from_user.id
    admin_username = message.from_user.username or "неизвестно"

    logger.info(
        "Обработка добавления пользователя от администратора tg_id: %s username: %s",
        admin_id,
        admin_username,
    )

    user_data = parse_data_from_text(text=message.text)
    await message.delete()

    if user_data is None:
        await _show_error_and_stay(
            bot=message.bot,
            chat_id=message.chat.id,
            active_message_id=active_message_id,
            text=Dialog.User.INVALID_USERNAME_FORMAT_ADD,
        )
        return

    tracking_dto = UserTrackingDTO(
        admin_username=admin_username,
        admin_tgid=str(admin_id),
        user_username=user_data.username,
        user_tgid=user_data.tg_id,
    )

    try:
        usecase: AddUserToTrackingUseCase = container.resolve(AddUserToTrackingUseCase)
        result = await usecase.execute(dto=tracking_dto)
    except Exception as e:
        logger.error(
            "Критическая ошибка при добавлении пользователя %s администратором %s: %s",
            user_data.username or user_data.tg_id,
            admin_username,
            e,
            exc_info=True,
        )
        await _show_error_and_stay(
            bot=message.bot,
            chat_id=message.chat.id,
            active_message_id=active_message_id,
            text=Dialog.UserTracking.ERROR_ADD_USER_TO_TRACKING,
        )
        return

    if not result.success:
        logger.info(
            "Ошибка добавления пользователя %s в отслеживание администратором %s: %s",
            user_data.username or user_data.tg_id,
            admin_username,
            result.message,
        )
        # Если пользователь уже отслеживается, предлагаем перейти к аналитике
        reply_markup = (
            move_to_analytics_ikb(user_id=result.user_id)
            if result.user_id
            else None  # _show_error_and_stay will use default
        )
        await _show_error_and_stay(
            bot=message.bot,
            chat_id=message.chat.id,
            active_message_id=active_message_id,
            text=result.message,
            reply_markup=reply_markup,
        )
        return

    logger.info(
        "Пользователь %s успешно добавлен администратором %s в отслеживание",
        user_data.username or user_data.tg_id,
        admin_username,
    )

    await message.answer(
        text=result.message,
        reply_markup=move_to_analytics_ikb(user_id=result.user_id),
    )

    get_tracked_chats_usecase: GetUserTrackedChatsUseCase = container.resolve(
        GetUserTrackedChatsUseCase
    )
    user_chats = await get_tracked_chats_usecase.execute(tg_id=str(admin_id))
    if user_chats.total_count == 0:
        await _show_error_and_stay(
            bot=message.bot,
            chat_id=message.chat.id,
            active_message_id=active_message_id,
            text=Dialog.UserAndChatsSettings.NO_CHATS_FOR_TIME_SETUP,
        )
        return

    first_chat = user_chats.chats[0]
    await state.update_data(
        chat_id=first_chat.id,
        start_time=None,
        end_time=None,
        tolerance=None,
        breaks_time=None,
    )
    await state.set_state(FirstTimeSetupStates.waiting_work_start)
    await _show_time_menu(
        bot=message.bot,
        chat_id=message.chat.id,
        message_id=active_message_id,
        state=state,
    )
