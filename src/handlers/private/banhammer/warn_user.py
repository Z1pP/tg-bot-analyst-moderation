import logging
from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from constants import KbCommands, Dialog
from constants.punishment import PunishmentActions as Actions
from container import container
from dto import ModerationActionDTO
from keyboards.inline.banhammer import no_reason_ikb
from keyboards.inline.chats_kb import tracked_chats_with_all_kb
from keyboards.reply import admin_menu_kb
from services import UserService
from states import BanHammerStates, WarnUserStates
from usecases.chat import GetChatsForUserActionUseCase
from usecases.moderation import GiveUserWarnUseCase
from utils.state_logger import log_and_set_state
from utils.user_data_parser import parse_data_from_text

router = Router()
logger = logging.getLogger(__name__)


@router.message(
    F.text == KbCommands.WARN_USER,
    BanHammerStates.block_menu,
)
async def warn_user_handler(message: types.Message, state: FSMContext) -> None:
    """Обработчик для предупреждения пользователя."""
    await message.reply(text=Dialog.WarnUser.INPUT_USER_DATA)
    await log_and_set_state(message, state, WarnUserStates.waiting_user_input)


@router.message(WarnUserStates.waiting_user_input)
async def process_user_data_input(message: types.Message, state: FSMContext) -> None:
    """Обработчик для получения данных о пользователе."""
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
            text=Dialog.WarnUser.USER_NOT_FOUND.format(
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
        f"{Dialog.WarnUser.INPUT_REASON}"
    )
    await message.reply(text=user_info, reply_markup=no_reason_ikb())
    await log_and_set_state(message, state, WarnUserStates.waiting_reason_input)


@router.callback_query(
    WarnUserStates.waiting_reason_input,
    F.data == "no_reason",
)
async def process_no_reason(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Обработчик для кнопки 'Без причины'."""
    await callback.answer()
    await _process_reason_and_select_chat(
        callback.message,
        state,
        None,
        from_user=callback.from_user,
    )


@router.message(WarnUserStates.waiting_reason_input)
async def process_reason_input(message: types.Message, state: FSMContext) -> None:
    """Обработчик для получения причины предупреждения."""
    reason = message.text.strip()
    await _process_reason_and_select_chat(
        message,
        state,
        reason,
        from_user=message.from_user,
    )


async def _process_reason_and_select_chat(
    message: types.Message,
    state: FSMContext,
    reason: str | None,
    from_user: types.User | None = None,
) -> None:
    """Общая логика обработки причины и выбора чата."""

    data = await state.get_data()
    user_tgid = data.get("tg_id")
    username = data.get("username")

    usecase: GetChatsForUserActionUseCase = container.resolve(
        GetChatsForUserActionUseCase
    )

    chat_dtos = await usecase.execute(
        admin_tgid=str(from_user.id),
        user_tgid=user_tgid,
    )

    if not chat_dtos:
        await message.answer(text=Dialog.WarnUser.NO_CHATS)
        await log_and_set_state(message, state, BanHammerStates.block_menu)
        return

    await state.update_data(reason=reason, chat_dtos=chat_dtos)

    await message.answer(
        text=Dialog.WarnUser.SELECT_CHAT.format(username=username),
        reply_markup=tracked_chats_with_all_kb(dtos=chat_dtos),
    )
    await log_and_set_state(message, state, WarnUserStates.waiting_chat_select)


@router.callback_query(
    WarnUserStates.waiting_chat_select,
    F.data.startswith("chat__"),
)
async def process_chat_selection(
    callback: types.CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработчик для выбора чата для предупреждения."""
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
        "Начало предупреждения пользователя %s в %d чатах",
        username,
        len(chat_dtos),
    )

    usecase: GiveUserWarnUseCase = container.resolve(GiveUserWarnUseCase)

    success_chats = []
    failed_chats = []

    for chat in chat_dtos:
        dto = ModerationActionDTO(
            action=Actions.WARNING,
            violator_tgid=user_tgid,
            violator_username=username,
            admin_tgid=str(callback.from_user.id),
            admin_username=callback.from_user.username,
            chat_tgid=chat.tg_id,
            chat_title=chat.title,
            reason=data.get("reason"),
            from_admin_panel=True,
        )

        try:
            await usecase.execute(dto=dto)
            success_chats.append(chat.title)
            logger.info("Предупреждение в чате %s успешно", chat.title)
        except Exception as e:
            failed_chats.append(chat.title)
            logger.error(
                "Ошибка предупреждения в чате %s: %s",
                chat.title,
                e,
                exc_info=True,
            )

    await callback.message.delete()

    if success_chats and not failed_chats:
        response_text = f"✅ Пользователь @{username} предупрежден!"
        if len(success_chats) > 1:
            response_text += (
                f"\n\nЧаты ({len(success_chats)}): {', '.join(success_chats)}"
            )
    elif success_chats and failed_chats:
        response_text = (
            f"⚠️ Пользователь @{username} частично предупрежден\n\n"
            f"✅ Успешно ({len(success_chats)}): {', '.join(success_chats)}\n"
            f"❌ Ошибки ({len(failed_chats)}): {', '.join(failed_chats)}"
        )
    else:
        response_text = f"❌ Не удалось предупредить @{username} ни в одном чате"

    await callback.message.answer(
        text=response_text,
        reply_markup=admin_menu_kb(),
    )
    await state.clear()
