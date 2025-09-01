import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from container import container
from usecases.report import GetBreaksDetailReportUseCase
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
        report_dto = data.get("report_dto")

        if not report_dto:
            await send_html_message_with_kb(
                message=callback.message,
                text="Не удалось получить данные для отчета",
            )
            return

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

    except Exception as e:
        await handle_exception(callback.message, e, "detailed_report_handler")
