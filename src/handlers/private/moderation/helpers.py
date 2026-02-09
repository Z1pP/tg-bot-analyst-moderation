"""Модуль вспомогательных функций для модерации.

Содержит общую логику для поиска пользователей, обработки ввода причин
и выполнения действий модерации (бан, предупреждение и т.д.).
"""

import logging
from typing import Optional, Type, Union

from aiogram import Bot, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State
from punq import Container

from constants import Dialog
from constants.punishment import PunishmentActions as Actions
from dto import ModerationActionDTO
from dto.chat_dto import ChatDTO
from keyboards.inline.chats import tracked_chats_with_all_ikb
from keyboards.inline.moderation import back_to_moderation_menu_ikb, moderation_menu_ikb
from services import UserService
from usecases.chat import GetChatsForUserActionUseCase
from usecases.moderation import GiveUserBanUseCase, GiveUserWarnUseCase
from utils.send_message import safe_edit_message
from utils.user_data_parser import parse_data_from_text

from .errors import handle_moderation_error

ModerationUsecase = Union[GiveUserWarnUseCase, GiveUserBanUseCase]

logger = logging.getLogger(__name__)


async def setup_user_input_view(
    callback: types.CallbackQuery,
    state: FSMContext,
    *,
    next_state: State,
    dialog_text: str,
) -> None:
    """Инициализирует процесс поиска пользователя, отображая приглашение к вводу.

    Args:
        callback: Объект callback-запроса от кнопки модерации.
        state: Контекст состояния FSM.
        next_state: Состояние, в которое нужно переключиться для ожидания ввода.
        dialog_text: Текст сообщения с инструкцией для пользователя.

    State:
        Устанавливает: next_state.
        Сохраняет: message_to_edit_id для последующего редактирования.
    """
    await callback.answer()
    await state.update_data(message_to_edit_id=callback.message.message_id)

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=dialog_text,
        reply_markup=back_to_moderation_menu_ikb(),
    )
    await state.set_state(next_state)


async def execute_moderation_logic(
    callback: types.CallbackQuery,
    state: FSMContext,
    action: Actions,
    usecase_cls: Type[ModerationUsecase],
    success_text: str,
    partial_text: str,
    fail_text: str,
    container: Container,
) -> None:
    """Выполняет действие модерации (бан/варн) в выбранных чатах.

    Args:
        callback: Объект callback-запроса с ID выбранного чата (или "all").
        state: Контекст состояния FSM.
        action: Тип выполняемого действия (Actions.BAN, Actions.WARNING).
        usecase_cls: Класс юзкейса для выполнения действия.
        success_text: Текст при успешном выполнении во всех чатах.
        partial_text: Текст при частичном успехе.
        fail_text: Текст при полной неудаче.
        container: DI-контейнер для разрешения зависимостей.

    State:
        Ожидает: данные о нарушителе (username, tg_id) и список чатов (chat_dtos).
    """
    data = await state.get_data()
    chat_id_from_callback = callback.data.split("__")[1]
    chat_dtos_data = data.get("chat_dtos")
    username = data.get("username")
    user_tgid = data.get("tg_id")

    if not chat_dtos_data or not username or not user_tgid:
        logger.error("Некорректные данные в state: %s", data)
        await handle_moderation_error(
            event=callback,
            state=state,
            text="❌ Ошибка: некорректные данные. Попробуйте снова.",
        )
        return

    chat_dtos = [ChatDTO.model_validate(chat) for chat in chat_dtos_data]

    if chat_id_from_callback != "all":
        chat_dtos = [
            chat for chat in chat_dtos if chat.id == int(chat_id_from_callback)
        ]

    logger.info(
        "Начало действия %s пользователя %s в %s чатах",
        action.value,
        username,
        len(chat_dtos),
    )

    usecase = container.resolve(usecase_cls)

    success_chats_titles: list[str] = []
    failed_chats_titles: list[str] = []

    for chat in chat_dtos:
        dto = ModerationActionDTO(
            action=action,
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
            success_chats_titles.append(chat.title)
            logger.info("Действие %s в чате %s успешно", action.value, chat.title)
        except Exception as e:
            failed_chats_titles.append(chat.title)
            logger.error(
                "Ошибка действия %s в чате %s: %s",
                action.value,
                chat.title,
                e,
                exc_info=True,
            )

    # Формирование ответа
    if success_chats_titles and not failed_chats_titles:
        if len(success_chats_titles) > 1:
            # Формируем блок с перечнем названий чатов
            titles_block = "\n".join(
                f"{i}. {title}" for i, title in enumerate(success_chats_titles, 1)
            )
        else:
            titles_block = success_chats_titles[0]

        response_text = success_text.format(
            username=username, chats_titles=titles_block
        )

    elif success_chats_titles and failed_chats_titles:
        response_text = partial_text.format(
            username=username,
            ok=", ".join(success_chats_titles),
            fail=", ".join(failed_chats_titles),
        )
    else:
        response_text = fail_text.format(username=username)

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=response_text,
        reply_markup=moderation_menu_ikb(),
    )


async def handle_user_search_logic(
    message: types.Message,
    state: FSMContext,
    bot: Bot,
    container: Container,
    *,
    dialog_texts: dict[str, str],
    success_keyboard: types.InlineKeyboardMarkup,
    next_state: State,
    show_block_actions_on_error: bool = False,
) -> None:
    """Обрабатывает ввод данных пользователя и выполняет поиск в базе.

    Args:
        message: Объект сообщения с введенными данными (username или ID).
        state: Контекст состояния FSM.
        bot: Экземпляр бота.
        container: DI-контейнер.
        dialog_texts: Словарь с текстами ответов (invalid_format, user_not_found, user_info).
        success_keyboard: Клавиатура, отображаемая при успешном нахождении пользователя.
        next_state: Состояние для перехода после успешного поиска.
        show_block_actions_on_error: Флаг для отображения меню модерации при ошибке.

    State:
        Устанавливает: next_state при успехе.
        Сохраняет: данные найденного пользователя (username, id, tg_id).
    """
    user_data = parse_data_from_text(text=message.text)
    await message.delete()

    data = await state.get_data()
    message_to_edit_id = data.get("message_to_edit_id")

    # --- Если данные пользователя не введены или введены некорректно
    if user_data is None:
        await handle_moderation_error(
            event=message,
            state=state,
            text=dialog_texts["invalid_format"],
            message_to_edit_id=message_to_edit_id,
            reply_markup=back_to_moderation_menu_ikb(),
        )
        return

    user_service: UserService = container.resolve(UserService)

    user = None

    user = await user_service.get_user(
        tg_id=user_data.tg_id, username=user_data.username
    )

    # --- Если пользователь не найден
    if user is None:
        identificator = user_data.tg_id or user_data.username
        await handle_moderation_error(
            event=message,
            state=state,
            text=dialog_texts["user_not_found"].format(identificator=identificator),
            message_to_edit_id=message_to_edit_id,
            reply_markup=back_to_moderation_menu_ikb(),
        )
        return

    await state.update_data(
        username=user.username,
        id=user.id,
        tg_id=user.tg_id,
    )

    if message_to_edit_id:
        await safe_edit_message(
            bot=bot,
            text=dialog_texts["user_info"].format(
                username=user.username,
                tg_id=user.tg_id,
            ),
            chat_id=message.chat.id,
            message_id=message_to_edit_id,
            reply_markup=success_keyboard(),
        )

    await state.set_state(next_state)


async def handle_reason_input_logic(
    reason: Optional[str],
    sender: Union[types.Message, types.CallbackQuery],
    state: FSMContext,
    bot: Bot,
    container: Container,
    is_callback: bool,
    next_state: State,
) -> None:
    """Обрабатывает ввод причины и подготавливает список доступных чатов.

    Args:
        reason: Текст причины или None.
        sender: Объект сообщения или callback-запроса.
        state: Контекст состояния FSM.
        bot: Экземпляр бота.
        container: DI-контейнер.
        is_callback: Флаг, указывающий, является ли отправитель callback-запросом.
        next_state: Состояние для перехода после обработки причины.

    State:
        Устанавливает: next_state при наличии доступных чатов.
        Сохраняет: причину (reason) и список чатов (chat_dtos).
    """
    chat_id = sender.message.chat.id if is_callback else sender.chat.id
    from_user_id = sender.from_user.id
    message_to_edit_id = None

    if not is_callback:
        await sender.delete()

    data = await state.get_data()
    user_tgid = data.get("tg_id")
    username = data.get("username")
    message_to_edit_id = data.get("message_to_edit_id")

    logger.info(
        "admin_id=%s, user_tgid=%s, username=%s, reason=%s",
        from_user_id,
        user_tgid,
        username,
        "<none>" if reason is None else reason,
    )

    usecase: GetChatsForUserActionUseCase = container.resolve(
        GetChatsForUserActionUseCase
    )
    chat_dtos = await usecase.execute(admin_tgid=str(from_user_id), user_tgid=user_tgid)

    if not chat_dtos:
        await handle_moderation_error(
            event=sender,
            state=state,
            text=Dialog.WarnUser.NO_CHATS.format(username=username),
            message_to_edit_id=message_to_edit_id,
        )

        logger.warning(
            "Отслеживаемы чаты не найдены для пользователя %s (%s)",
            username,
            user_tgid,
        )
        return

    await state.update_data(
        reason=reason,
        chat_dtos=[chat.model_dump(mode="json") for chat in chat_dtos],
    )

    await safe_edit_message(
        bot=bot,
        chat_id=chat_id,
        message_id=message_to_edit_id,
        text=Dialog.WarnUser.SELECT_CHAT.format(username=username),
        reply_markup=tracked_chats_with_all_ikb(dtos=chat_dtos),
    )

    await state.set_state(next_state)
