import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from dto import UserTrackingDTO
from keyboards.inline.users import (
    back_to_users_menu_ikb,
    hide_notification_ikb,
    move_to_analytics_ikb,
)
from states.user import UsernameStates
from usecases.user_tracking import AddUserToTrackingUseCase
from utils.send_message import safe_edit_message
from utils.user_data_parser import parse_data_from_text

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data == CallbackData.User.ADD)
async def add_user_to_tracking_handler(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """
    Хендлер для обработки добавления пользователя в список отслеживания.
    """
    await callback.answer()

    logger.info(
        "Администратор tg_id: %s username: %s начал добавление "
        "нового пользователя в отслеживание",
        callback.from_user.id,
        callback.from_user.username,
    )

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.User.ADD_USER_INFO,
        reply_markup=back_to_users_menu_ikb(),
    )

    await state.set_state(UsernameStates.waiting_add_user_data_input)


@router.message(UsernameStates.waiting_add_user_data_input)
async def process_adding_user(
    message: Message,
    state: FSMContext,
    container: Container,
) -> None:
    """Обработчик для получения @username и ID пользователя."""
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
        await message.answer(
            text=Dialog.User.INVALID_USERNAME_FORMAT_ADD,
            reply_markup=hide_notification_ikb(),
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
        await message.answer(
            text=Dialog.UserTracking.ERROR_ADD_USER_TO_TRACKING,
            reply_markup=hide_notification_ikb(),
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
            else hide_notification_ikb()
        )

        await message.answer(
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
