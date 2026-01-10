from aiogram import F, Router, types
from punq import Container

from constants.period import TimePeriod
from usecases.report.chat.send_daily_chat_reports import SendDailyChatReportsUseCase

router = Router(name=__name__)


@router.message(F.text.startswith("report"))
async def send_daily_chat_reports(message: types.Message, container: Container):
    try:
        usecase: SendDailyChatReportsUseCase = container.resolve(
            SendDailyChatReportsUseCase
        )
        await usecase.execute(TimePeriod.TODAY.value)
    except Exception as e:
        await message.answer(f"Ошибка при отправке ежедневных отчетов: {e}")
