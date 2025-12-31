import logging
from dataclasses import dataclass

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from constants import Dialog
from constants.callback import CallbackData
from container import container
from dto import UserTrackingDTO
from keyboards.inline.users import cancel_add_user_ikb, users_menu_ikb
from states import UserStateManager
from states.user import UsernameStates
from usecases.user_tracking import AddUserToTrackingUseCase
from utils.exception_handler import handle_exception
from utils.send_message import safe_edit_message
from utils.user_data_parser import parse_data_from_text

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ParsedData:
    username: str
    user_tgid: str


@router.callback_query(F.data == CallbackData.User.ADD)
async def add_user_to_tracking_handler(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """
    Хендлер для обработки добавления пользователя в список отслеживания.
    """
    await callback.answer()

    try:
        logger.info(
            f"Пользователь {callback.from_user.id} начал добавление "
            "нового пользователя в отслеживание"
        )

        await callback.message.edit_text(
            text=Dialog.User.INPUT_USERNAME,
            reply_markup=cancel_add_user_ikb(),
        )

        await state.update_data(active_message_id=callback.message.message_id)

        await state.set_state(UsernameStates.waiting_user_data_input)
    except Exception as e:
        await handle_exception(callback.message, e, "add_user_to_tracking_handler")


@router.callback_query(F.data == CallbackData.User.CANCEL_ADD)
async def cancel_add_user_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик отмены добавления пользователя"""
    await callback.answer()
    await state.clear()

    await callback.message.edit_text(
        text=Dialog.User.ACTION_CANCELLED,
        reply_markup=users_menu_ikb(),
    )

    await state.set_state(UserStateManager.users_menu)


@router.message(UsernameStates.waiting_user_data_input)
async def process_adding_user(message: Message, state: FSMContext) -> None:
    """
    Обработчик для получения @username и ID пользователя.
    """
    try:
        admin_username = message.from_user.username
        logger.info(f"Обработка добавления пользователя от {admin_username}")

        data = await state.get_data()
        active_message_id = data.get("active_message_id")

        try:
            user_data = parse_data_from_text(text=message.text)
        except ValueError:
            if active_message_id:
                await safe_edit_message(
                    bot=message.bot,
                    chat_id=message.chat.id,
                    message_id=active_message_id,
                    text=Dialog.User.INVALID_USERNAME_FORMAT,
                    reply_markup=cancel_add_user_ikb(),
                )
            await message.delete()
            return

        if user_data is None:
            text = Dialog.User.INVALID_FORMAT_RETRY
            if active_message_id:
                await safe_edit_message(
                    bot=message.bot,
                    chat_id=message.chat.id,
                    message_id=active_message_id,
                    text=text,
                    reply_markup=cancel_add_user_ikb(),
                )
            await message.delete()
            return

        tracking_dto = UserTrackingDTO(
            admin_username=admin_username,
            admin_tgid=str(message.from_user.id),
            user_username=user_data.username,
            user_tgid=user_data.tg_id,
        )

        usecase: AddUserToTrackingUseCase = container.resolve(AddUserToTrackingUseCase)
        result = await usecase.execute(dto=tracking_dto)

        await message.delete()

        if not result.success:
            logger.info(
                f"Ошибка добавления пользователя {user_data.username} в отслеживание"
            )
            if active_message_id:
                await safe_edit_message(
                    bot=message.bot,
                    chat_id=message.chat.id,
                    message_id=active_message_id,
                    text=result.message,
                    reply_markup=users_menu_ikb(),
                )
            return

        logger.info(
            f"Пользователь {user_data.username} успешно добавлен администратором {admin_username}"
        )

        if active_message_id:
            await safe_edit_message(
                bot=message.bot,
                chat_id=message.chat.id,
                message_id=active_message_id,
                text=result.message,
                reply_markup=users_menu_ikb(),
            )

        await state.set_state(UserStateManager.users_menu)
    except Exception as e:
        await handle_exception(message, e, "process_adding_user")
