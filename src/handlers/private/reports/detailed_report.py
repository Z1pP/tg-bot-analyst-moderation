import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from container import container
from dto.report import AllUsersReportDTO, ChatReportDTO
from keyboards.inline.report import hide_details_ikb
from usecases.report import (
    GetAllUsersBreaksDetailReportUseCase,
    GetBreaksDetailReportUseCase,
    GetChatBreaksDetailReportUseCase,
)
from utils.exception_handler import handle_exception
from utils.send_message import (
    safe_edit_message,
    safe_edit_message_reply_markup,
    send_html_message_with_kb,
)

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "order_details")
async def detailed_report_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
) -> None:
    try:
        await callback.answer()

        data = await state.get_data()
        logger.info(f"Данные из состояния: {list(data.keys())}")

        # Проверяем какой тип отчета - одиночный, для всех пользователей или для чата
        single_user_dto = data.get("report_dto")
        all_users_dto = data.get("all_users_report_dto")
        chat_dto = data.get("chat_report_dto")

        logger.info(
            f"single_user_dto: {type(single_user_dto) if single_user_dto else None}"
        )
        logger.info(f"all_users_dto: {type(all_users_dto) if all_users_dto else None}")
        logger.info(f"chat_dto: {type(chat_dto) if chat_dto else None}")

        if single_user_dto:
            await _handle_single_user_details(callback, single_user_dto)
        elif all_users_dto:
            await _handle_all_users_details(callback, all_users_dto)
        elif chat_dto:
            await _handle_chat_details(callback, chat_dto)
        else:
            await send_html_message_with_kb(
                message=callback.message,
                text="Не удалось получить данные для отчета",
            )

    except Exception as e:
        await handle_exception(callback.message, e, "detailed_report_handler")


async def _handle_single_user_details(
    callback: types.CallbackQuery, report_dto
) -> None:
    """Обрабатывает детализацию для одного пользователя"""
    usecase: GetBreaksDetailReportUseCase = container.resolve(
        GetBreaksDetailReportUseCase
    )
    report_parts = await usecase.execute(report_dto)

    message_ids = []
    for part in report_parts:
        sent_message = await send_html_message_with_kb(
            message=callback.message,
            text=part,
        )
        message_ids.append(sent_message.message_id)

    # Добавляем кнопку "Скрыть детализацию" к последнему сообщению
    if message_ids:
        last_message_id = message_ids[-1]
        await safe_edit_message_reply_markup(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=last_message_id,
            reply_markup=hide_details_ikb(message_ids),
        )

    logger.info(
        f"Детализация перерывов отправлена для пользователя {report_dto.user_id}"
    )


async def _handle_all_users_details(callback: types.CallbackQuery, report_dto) -> None:
    """Обрабатывает детализацию для всех пользователей"""
    # Проверяем что это правильный тип DTO
    if not isinstance(report_dto, AllUsersReportDTO):
        await send_html_message_with_kb(
            message=callback.message,
            text="Ошибка: неверный тип данных для детализации",
        )
        return

    usecase: GetAllUsersBreaksDetailReportUseCase = container.resolve(
        GetAllUsersBreaksDetailReportUseCase
    )
    report_parts = await usecase.execute(report_dto)

    message_ids = []
    for part in report_parts:
        sent_message = await send_html_message_with_kb(
            message=callback.message,
            text=part,
        )
        message_ids.append(sent_message.message_id)

    # Добавляем кнопку "Скрыть детализацию" к последнему сообщению
    if message_ids:
        last_message_id = message_ids[-1]
        await safe_edit_message_reply_markup(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=last_message_id,
            reply_markup=hide_details_ikb(message_ids),
        )

    logger.info(
        f"Детализация перерывов отправлена для всех пользователей админа {report_dto.user_tg_id}"
    )


async def _handle_chat_details(callback: types.CallbackQuery, report_dto) -> None:
    """Обрабатывает детализацию для отчета по чату"""
    # Проверяем что это правильный тип DTO
    if not isinstance(report_dto, ChatReportDTO):
        await send_html_message_with_kb(
            message=callback.message,
            text="Ошибка: неверный тип данных для детализации",
        )
        return

    usecase: GetChatBreaksDetailReportUseCase = container.resolve(
        GetChatBreaksDetailReportUseCase
    )
    report_parts = await usecase.execute(report_dto)

    message_ids = []
    for part in report_parts:
        sent_message = await send_html_message_with_kb(
            message=callback.message,
            text=part,
        )
        message_ids.append(sent_message.message_id)

    # Добавляем кнопку "Скрыть детализацию" к последнему сообщению
    if message_ids:
        last_message_id = message_ids[-1]
        await safe_edit_message_reply_markup(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=last_message_id,
            reply_markup=hide_details_ikb(message_ids),
        )

    logger.info(f"Детализация перерывов отправлена для чата {report_dto.chat_id}")


@router.callback_query(F.data.startswith("hide_details_"))
async def hide_details_handler(callback: types.CallbackQuery) -> None:
    """Обработчик скрытия детализации (одно или несколько сообщений)"""
    try:
        # Извлекаем ID сообщений из callback_data
        message_ids_str = callback.data.replace("hide_details_", "")
        message_ids = [int(msg_id) for msg_id in message_ids_str.split(",") if msg_id]

        if not message_ids:
            await callback.answer("❌ Ошибка: не найдены ID сообщений", show_alert=True)
            return

        # Удаляем все сообщения детализации
        deleted_count = 0
        for msg_id in message_ids:
            try:
                await callback.bot.delete_message(
                    chat_id=callback.message.chat.id,
                    message_id=msg_id,
                )
                deleted_count += 1
            except Exception as e:
                logger.warning(f"Не удалось удалить сообщение {msg_id}: {e}")

        # Удаляем само сообщение с кнопкой, если оно существует
        if callback.message:
            try:
                await callback.message.delete()
            except Exception:
                pass

        if deleted_count > 0:
            await callback.answer("✅ Детализация скрыта")
        else:
            await callback.answer("❌ Не удалось скрыть детализацию", show_alert=True)

    except Exception as e:
        logger.error(f"Ошибка при скрытии детализации: {e}", exc_info=True)
        # Пытаемся отредактировать сообщение с ошибкой
        if callback.message:
            success = await safe_edit_message(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text="❌ Ошибка при скрытии детализации",
            )
            if not success:
                await callback.answer(
                    "❌ Ошибка при скрытии детализации", show_alert=True
                )
        else:
            await callback.answer("❌ Ошибка при скрытии детализации", show_alert=True)

