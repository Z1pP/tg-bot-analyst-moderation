import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from constants.callback import CallbackData
from container import container
from keyboards.inline.chats import cancel_archive_time_setting_ikb
from services.report_schedule_service import ReportScheduleService
from services.user import UserService
from states import ChatArchiveState
from utils.data_parser import parse_time
from utils.send_message import safe_edit_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data == CallbackData.Chat.ARCHIVE_TIME_SETTING)
async def change_sending_time_handler(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработчик для изменения/установки времени отрпавки отчета"""
    await callback.answer()

    msg_text = (
        "Пожалуйста, пришлите время, когда будет автоматически отправляться "
        "ежедневный отчёт в формате HH:mm\n\n"
        "Например: 23:45"
    )

    msg = await callback.message.edit_text(
        text=msg_text,
        reply_markup=cancel_archive_time_setting_ikb(),
    )

    await state.update_data(active_message_id=msg.message_id)

    await state.set_state(ChatArchiveState.waiting_time_input)


@router.message(ChatArchiveState.waiting_time_input)
async def time_input_handler(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    active_message_id = data.get("active_message_id")
    chat_id = data.get("chat_id")

    parsed_time = parse_time(text=message.text)

    if not parsed_time:
        if active_message_id:
            text = (
                "❌ Неверный формат времени!\n\n"
                "Пожалуйста, пришлите время в&nbsp;формате HH:mm.\n\n"
                "Например: 23:45"
            )
            await safe_edit_message(
                bot=message.bot,
                chat_id=message.chat.id,
                message_id=active_message_id,
                text=text,
                reply_markup=cancel_archive_time_setting_ikb(),
            )

        await message.delete()
        return

    if not chat_id:
        logger.error("chat_id не найден в state")
        await message.delete()
        return

    try:
        # Получаем пользователя из БД
        user_service: UserService = container.resolve(UserService)
        user = await user_service.get_user(tg_id=str(message.from_user.id))

        if not user:
            logger.error("Пользователь не найден в БД: tg_id=%s", message.from_user.id)
            text = "❌ Ошибка: пользователь не найден в системе."
            if active_message_id:
                await safe_edit_message(
                    bot=message.bot,
                    chat_id=message.chat.id,
                    message_id=active_message_id,
                    text=text,
                    reply_markup=cancel_archive_time_setting_ikb(),
                )
            await message.delete()
            return

        # Сохраняем или обновляем расписание
        schedule_service: ReportScheduleService = container.resolve(
            ReportScheduleService
        )

        schedule = await schedule_service.get_schedule(user_id=user.id, chat_id=chat_id)

        if schedule:
            # Обновляем существующее расписание
            await schedule_service.update_sending_time(
                user_id=user.id, chat_id=chat_id, new_time=parsed_time
            )
        else:
            # Создаем новое расписание
            await schedule_service.get_or_create_schedule(
                user_id=user.id,
                chat_id=chat_id,
                sent_time=parsed_time,
                enabled=True,
            )

        text = (
            "✅ Время успешно применено!\n\n"
            f"Ежедневный отчёт будет приходить в архив в {parsed_time.strftime('%H:%M')}."
        )

        await safe_edit_message(
            bot=message.bot,
            chat_id=message.chat.id,
            message_id=active_message_id,
            text=text,
            reply_markup=cancel_archive_time_setting_ikb(),
        )

        await message.delete()

    except Exception as e:
        logger.error("Ошибка при сохранении времени отправки: %s", e, exc_info=True)
        text = "❌ Произошла ошибка при сохранении времени. Попробуйте позже."
        if active_message_id:
            await safe_edit_message(
                bot=message.bot,
                chat_id=message.chat.id,
                message_id=active_message_id,
                text=text,
                reply_markup=cancel_archive_time_setting_ikb(),
            )
        await message.delete()
