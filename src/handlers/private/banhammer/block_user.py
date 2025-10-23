import logging
from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext

from constants import KbCommands, Dialog
from dto import AdminPanelBanDTO
from keyboards.inline.chats_kb import tracked_chats_with_all_kb
from keyboards.reply import admin_menu_kb
from services import UserService
from states import BanUserStates, BanHammerStates
from usecases.chat import GetChatsForUserActionUseCase
from usecases.moderation import BanUserFromAdminPanelUseCase
from utils.state_logger import log_and_set_state
from utils.user_data_parser import parse_data_from_text
from container import container


router = Router()
logger = logging.getLogger(__name__)


@router.message(
    F.text == KbCommands.BLOCK_USER,
    BanHammerStates.block_menu,
)
async def block_user_handler(message: types.Message, state: FSMContext) -> None:
    """
    Обработчик для блокировки пользователя.
    """
    await message.reply(text=Dialog.BanUser.INPUT_USER_DATA)
    await log_and_set_state(message, state, BanUserStates.waiting_user_input)


@router.message(BanUserStates.waiting_user_input)
async def process_user_data_input(message: types.Message, state: FSMContext) -> None:
    """
    Обработчик для получения данных о пользователе.
    """
    user_data = parse_data_from_text(text=message.text)

    if user_data is None:
        await message.reply(text=Dialog.Error.INVALID_USERNAME_FORMAT)
        return

    user_service: UserService = container.resolve(UserService)

    user = None

    if user_data.tg_id:
        user = await user_service.get_user(tg_id=user_data.tg_id)
    elif user_data.username:
        user = await user_service.get_by_username(username=user_data.username)

    if user is None:
        identificator = (
            f"<code>{user_data.tg_id}</code>"
            if user_data.tg_id
            else f"<b>@{user_data.username}</b>"
        )
        await message.reply(
            text=Dialog.BanUser.USER_NOT_FOUND.format(
                identificator=identificator,
            )
        )
        return

    await state.update_data(
        username=user.username,
        id=user.id,
        tg_id=user.tg_id,
    )

    user_info = (
        f"👤 <b>Найден пользователь:</b>\n"
        f"• Юзер: @{user.username}\n"
        f"• ID: <code>{user.tg_id}</code>\n\n"
        f"{Dialog.BanUser.INPUT_REASON}"
    )
    await message.reply(text=user_info)
    await log_and_set_state(message, state, BanUserStates.waiting_reason_input)


@router.message(BanUserStates.waiting_reason_input)
async def process_reason_input(message: types.Message, state: FSMContext) -> None:
    """
    Обработчик для получения причины блокировки.
    """

    reason = message.text.strip()

    if len(reason) < 3:
        await message.reply(text="❌ Причина слишком короткая. Минимум 3 символа.")
        return

    if len(reason) > 32:
        await message.reply(text="❌ Причина слишком длинная. Максимум 32 символа.")
        return

    data = await state.get_data()
    user_tgid = data.get("tg_id")
    username = data.get("username")

    usecase: GetChatsForUserActionUseCase = container.resolve(
        GetChatsForUserActionUseCase
    )

    chat_dtos = await usecase.execute(
        admin_tgid=str(message.from_user.id),
        user_tgid=user_tgid,
    )

    if not chat_dtos:
        await message.reply(text=Dialog.BanUser.NO_CHATS)
        await log_and_set_state(message, state, BanHammerStates.block_menu)
        return

    await state.update_data(reason=reason, chat_dtos=chat_dtos)

    await message.reply(
        text=Dialog.BanUser.SELECT_CHAT.format(username=username),
        reply_markup=tracked_chats_with_all_kb(dtos=chat_dtos),
    )
    await log_and_set_state(message, state, BanUserStates.waiting_chat_select)


@router.callback_query(
    BanUserStates.waiting_chat_select,
    F.data.startswith("chat__"),
)
async def process_chat_selection(
    callback: types.CallbackQuery,
    state: FSMContext,
) -> None:
    """
    Обработчик для выбора чата для блокировки.
    """
    await callback.answer()

    data = await state.get_data()
    chat_id = callback.data.split("__")[1]
    chat_dtos = data.get("chat_dtos")
    username = data.get("username")
    user_tgid = data.get("tg_id")

    if not chat_dtos or not username or not user_tgid:
        logger.error("Некорректные данные в state: %s", data)
        await callback.message.answer(
            text="❌ Ошибка: некорректные данные. Попробуйте снова.",
            reply_markup=admin_menu_kb(),
        )
        await state.clear()
        return

    if chat_id != "all":
        chat_dtos = [chat for chat in chat_dtos if chat.id == int(chat_id)]

    logger.info(
        "Начало блокировки пользователя %s в %d чатах",
        username,
        len(chat_dtos),
    )

    usecase: BanUserFromAdminPanelUseCase = container.resolve(
        BanUserFromAdminPanelUseCase
    )

    success_chats = []
    failed_chats = []

    for chat in chat_dtos:
        dto = AdminPanelBanDTO(
            user_tgid=user_tgid,
            user_username=username,
            admin_tgid=str(callback.from_user.id),
            admin_username=callback.from_user.username,
            chat_tgid=chat.tg_id,
            chat_title=chat.title,
            reason=data.get("reason"),
        )

        try:
            await usecase.execute(dto=dto)
            success_chats.append(chat.title)
            logger.info("Блокировка в чате %s успешна", chat.title)
        except Exception as e:
            failed_chats.append(chat.title)
            logger.error(
                "Ошибка блокировки в чате %s: %s",
                chat.title,
                e,
                exc_info=True,
            )

    await callback.message.delete()

    if success_chats and not failed_chats:
        response_text = f"✅ Пользователь @{username} заблокирован!"
        if len(success_chats) > 1:
            response_text += (
                f"\n\nЧаты ({len(success_chats)}): {', '.join(success_chats)}"
            )
    elif success_chats and failed_chats:
        response_text = (
            f"⚠️ Пользователь @{username} частично заблокирован\n\n"
            f"✅ Успешно ({len(success_chats)}): {', '.join(success_chats)}\n"
            f"❌ Ошибки ({len(failed_chats)}): {', '.join(failed_chats)}"
        )
    else:
        response_text = f"❌ Не удалось заблокировать @{username} ни в одном чате"

    await callback.message.answer(
        text=response_text,
        reply_markup=admin_menu_kb(),
    )
    await state.clear()
