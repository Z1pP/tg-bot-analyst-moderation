import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from dto import UserTrackingDTO
from keyboards.inline.users import back_to_users_menu_ikb, users_menu_ikb
from states import UserStateManager
from states.user import UsernameStates
from usecases.user_tracking import AddUserToTrackingUseCase, HasTrackedUsersUseCase
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

    await state.update_data(active_message_id=callback.message.message_id)

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

    data = await state.get_data()
    active_message_id = data.get("active_message_id")

    user_data = parse_data_from_text(text=message.text)
    await message.delete()

    if user_data is None:
        if active_message_id:
            await safe_edit_message(
                bot=message.bot,
                chat_id=message.chat.id,
                message_id=active_message_id,
                text=Dialog.User.INVALID_USERNAME_FORMAT,
                reply_markup=back_to_users_menu_ikb(),
            )
        return

    tracking_dto = UserTrackingDTO(
        admin_username=admin_username,
        admin_tgid=str(admin_id),
        user_username=user_data.username,
        user_tgid=user_data.tg_id,
    )

    usecase: AddUserToTrackingUseCase = container.resolve(AddUserToTrackingUseCase)
    has_tracked_users_usecase: HasTrackedUsersUseCase = container.resolve(
        HasTrackedUsersUseCase
    )

    try:
        result = await usecase.execute(dto=tracking_dto)
    except Exception as e:
        logger.error(
            "Критическая ошибка при добавлении пользователя %s администратором %s: %s",
            user_data.username or user_data.tg_id,
            admin_username,
            e,
            exc_info=True,
        )
        if active_message_id:
            has_tracked_users = await has_tracked_users_usecase.execute(
                admin_tgid=str(admin_id)
            )
            await safe_edit_message(
                bot=message.bot,
                chat_id=message.chat.id,
                message_id=active_message_id,
                text=Dialog.UserTracking.ERROR_ADD_USER_TO_TRACKING,
                reply_markup=users_menu_ikb(has_tracked_users=has_tracked_users),
            )
        return

    has_tracked_users = await has_tracked_users_usecase.execute(
        admin_tgid=str(admin_id)
    )

    if not result.success:
        logger.info(
            "Ошибка добавления пользователя %s в отслеживание администратором %s: %s",
            user_data.username or user_data.tg_id,
            admin_username,
            result.message,
        )
        if active_message_id:
            await safe_edit_message(
                bot=message.bot,
                chat_id=message.chat.id,
                message_id=active_message_id,
                text=result.message,
                reply_markup=users_menu_ikb(has_tracked_users=has_tracked_users),
            )
        return

    logger.info(
        "Пользователь %s успешно добавлен администратором %s в отслеживание",
        user_data.username or user_data.tg_id,
        admin_username,
    )

    if active_message_id:
        await safe_edit_message(
            bot=message.bot,
            chat_id=message.chat.id,
            message_id=active_message_id,
            text=result.message,
            reply_markup=users_menu_ikb(has_tracked_users=has_tracked_users),
        )

    await state.set_state(UserStateManager.users_menu)
