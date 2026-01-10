import logging

from aiogram import F, Router, types
from aiogram.filters import Command
from punq import Container

from filters.admin_filter import StaffOnlyFilter
from mappers import map_message_to_moderation_dto
from usecases.moderation import GiveUserWarnUseCase

logger = logging.getLogger(__name__)
router = Router(name=__name__)


@router.message(
    Command("warn"),
    StaffOnlyFilter(),
    F.reply_to_message,
)
async def warn_user_handler(message: types.Message, container: Container) -> None:
    """
    Обрабатывает команду /warn для выдачи предупреждения пользователю.

    Команда должна быть ответом на сообщение нарушителя.
    Формат: /warn [причина]
    """
    dto = map_message_to_moderation_dto(message=message)

    try:
        usecase: GiveUserWarnUseCase = container.resolve(GiveUserWarnUseCase)
        await usecase.execute(dto=dto)
    except Exception as e:
        logger.error(f"Ошибка при выдаче предупреждения: {e}")
        return
