from aiogram import F, Router, types
from punq import Container

from constants.period import TimePeriod
from dto.chat_dto import GetChatWithArchiveDTO
from usecases.chat import GetChatWithArchiveUseCase
from usecases.report.chat.send_daily_chat_reports import SendDailyChatReportsUseCase

router = Router(name=__name__)


@router.message(F.text.startswith("report"))
async def send_daily_chat_reports(message: types.Message, container: Container) -> None:
    try:
        get_chat_uc: GetChatWithArchiveUseCase = container.resolve(
            GetChatWithArchiveUseCase
        )
        chat = await get_chat_uc.execute(
            GetChatWithArchiveDTO(chat_tgid=str(message.chat.id))
        )
        if chat is None:
            await message.answer("Чат не найден.")
            return

        usecase: SendDailyChatReportsUseCase = container.resolve(
            SendDailyChatReportsUseCase
        )
        await usecase.execute(chat_id=chat.id, period=TimePeriod.TODAY.value)
    except Exception as e:
        await message.answer(f"Ошибка при отправке ежедневных отчетов: {e}")
