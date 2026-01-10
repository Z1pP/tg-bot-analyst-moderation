import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from constants.enums import SummaryType
from constants.period import SummaryTimePeriod
from keyboards.inline.chats import chat_actions_ikb, summary_type_ikb
from keyboards.inline.report import hide_details_ikb
from services.chat import ChatService
from states import ChatStateManager
from usecases.summarize.summarize_chat_messages import GetChatSummaryUseCase
from utils.send_message import (
    safe_edit_message,
    send_split_html_message,
)

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(
    F.data == CallbackData.Chat.GET_CHAT_SUMMARY_24H,
    ChatStateManager.selecting_chat,
)
async def process_get_chat_summary_handler(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Обработчик запроса на выбор типа ИИ-сводки по чату за последние 24 часа."""
    await callback.answer()

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text="Выберите тип сводки:",
        reply_markup=summary_type_ikb(),
    )


@router.callback_query(
    F.data.startswith(CallbackData.Chat.PREFIX_CHAT_SUMMARY_TYPE),
    ChatStateManager.selecting_chat,
)
async def process_summary_type_selection_handler(
    callback: CallbackQuery, state: FSMContext, container: Container
) -> None:
    """Обработчик выбора типа сводки и её генерации."""
    await callback.answer()

    summary_type_str = callback.data.replace(
        CallbackData.Chat.PREFIX_CHAT_SUMMARY_TYPE, ""
    )
    summary_type = SummaryType(summary_type_str)

    data = await state.get_data()
    chat_id = data.get("chat_id")

    if not chat_id:
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Chat.CHAT_NOT_FOUND_OR_ALREADY_REMOVED,
            reply_markup=chat_actions_ikb(),
        )
        return

    # Получаем информацию о чате для возврата к dashboard
    chat_service: ChatService = container.resolve(ChatService)
    chat = await chat_service.get_chat_with_archive(chat_id=chat_id)

    # 1. Показываем статус выполнения в текущем сообщении
    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text="⏳ <b>Сводка на этапе выполнения</b>\nПожалуйста, подождите, это может занять до 30 секунд...",
    )

    try:
        # 2. Подготовка дат для 24ч
        start_date, end_date = SummaryTimePeriod.to_datetime(
            SummaryTimePeriod.LAST_24_HOURS.value
        )

        # 3. Вызываем UseCase
        usecase: GetChatSummaryUseCase = container.resolve(GetChatSummaryUseCase)
        summary = await usecase.execute(
            chat_id=chat_id,
            summary_type=summary_type,
            admin_tg_id=str(callback.from_user.id),
            start_date=start_date,
            end_date=end_date,
        )

        # 4. Отправляем ОТДЕЛЬНОЕ сообщение с результатом и кнопкой "Скрыть"
        message_ids = await send_split_html_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            text=summary,
        )

        # Добавляем кнопку "Скрыть" (удаляет все сообщения этой последовательности)
        # Прикрепляем её к последнему сообщению
        if message_ids:
            await callback.bot.edit_message_reply_markup(
                chat_id=callback.message.chat.id,
                message_id=message_ids[-1],
                reply_markup=hide_details_ikb(message_ids),
            )

        # 5. Возвращаем исходное сообщение к виду Dashboard
        if chat:
            await safe_edit_message(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=Dialog.Chat.CHAT_ACTIONS.format(
                    title=chat.title,
                    start_time=chat.start_time.strftime("%H:%M"),
                    end_time=chat.end_time.strftime("%H:%M"),
                ),
                reply_markup=chat_actions_ikb(),
            )
        else:
            await safe_edit_message(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text="✅ Сводка готова! Она отправлена отдельным сообщением.",
                reply_markup=chat_actions_ikb(),
            )

    except Exception as e:
        logger.error(
            f"Ошибка при генерации сводки для чата {chat_id}: {e}", exc_info=True
        )
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text="❌ Произошла ошибка при генерации сводки. Попробуйте позже.",
            reply_markup=chat_actions_ikb(),
        )
