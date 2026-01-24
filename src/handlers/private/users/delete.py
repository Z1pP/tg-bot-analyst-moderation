import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from dto import RemoveUserTrackingDTO
from keyboards.inline.users import (
    back_to_users_menu_ikb,
    hide_notification_ikb,
)
from states import UsernameStates
from usecases.user_tracking import (
    RemoveUserFromTrackingUseCase,
)
from utils.send_message import safe_edit_message
from utils.user_data_parser import parse_data_from_text

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data == CallbackData.User.REMOVE)
async def remove_user_from_tracking_handler(
    callback: CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    """
    Обработчик для удаления пользователя из списка отслеживания.
    """
    await callback.answer()
    await state.clear()

    logger.info(
        "Администратор tg_id: %s username: %s начал удаление "
        "пользователя из отслеживания",
        callback.from_user.id,
        callback.from_user.username,
    )

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.User.REMOVE_USER_INFO,
        reply_markup=back_to_users_menu_ikb(),
    )

    await state.set_state(UsernameStates.waiting_remove_user_data_input)


@router.message(UsernameStates.waiting_remove_user_data_input)
async def process_removing_user(
    message: Message,
    state: FSMContext,
    container: Container,
) -> None:
    """
    Обработчик для получения ID выбранного пользователя на удаление.
    """

    admin_id = message.from_user.id
    admin_username = message.from_user.username or "неизвестно"

    logger.info(
        "Обработка удаления пользователя от администратора tg_id: %s username: %s",
        admin_id,
        admin_username,
    )

    user_data = parse_data_from_text(text=message.text)
    await message.delete()

    if user_data is None:
        await message.answer(
            text=Dialog.User.INVALID_USERNAME_FORMAT_REMOVE,
            reply_markup=hide_notification_ikb(),
        )
        return

    dto = RemoveUserTrackingDTO(
        admin_username=admin_username,
        admin_tgid=str(admin_id),
        user_tgid=user_data.tg_id,
        user_username=user_data.username,
    )

    try:
        usecase: RemoveUserFromTrackingUseCase = container.resolve(
            RemoveUserFromTrackingUseCase
        )
        success = await usecase.execute(dto=dto)
    except Exception as e:
        logger.error(
            "Критическая ошибка при удалении пользователя %s администратором %s: %s",
            user_data.username or user_data.tg_id,
            admin_username,
            e,
            exc_info=True,
        )
        await message.answer(
            text=Dialog.UserTracking.ERROR_REMOVE_USER_FROM_TRACKING,
            reply_markup=hide_notification_ikb(),
        )
        return

    if success:
        await message.answer(
            text=Dialog.User.USER_REMOVED,
            reply_markup=hide_notification_ikb(),
        )
    else:
        await message.answer(
            text=Dialog.UserTracking.USER_NOT_FOUND_OR_ALREADY_REMOVED,
            reply_markup=hide_notification_ikb(),
        )
