import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from container import container
from dto.report import AllUsersReportDTO, ChatReportDTO
from usecases.report import (
    GetAllUsersBreaksDetailReportUseCase,
    GetBreaksDetailReportUseCase,
    GetChatBreaksDetailReportUseCase,
)
from utils.exception_handler import handle_exception
from utils.send_message import send_html_message_with_kb

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

    for part in report_parts:
        await send_html_message_with_kb(
            message=callback.message,
            text=part,
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

    for part in report_parts:
        await send_html_message_with_kb(
            message=callback.message,
            text=part,
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

    for part in report_parts:
        await send_html_message_with_kb(
            message=callback.message,
            text=part,
        )

    logger.info(f"Детализация перерывов отправлена для чата {report_dto.chat_id}")
