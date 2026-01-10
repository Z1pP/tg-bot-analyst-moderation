import logging

from aiogram import F, Router, types
from aiogram.filters import Command
from punq import Container

from filters.admin_filter import StaffOnlyFilter
from mappers import map_message_to_moderation_dto
from usecases.moderation import GiveUserBanUseCase

logger = logging.getLogger(__name__)
router = Router(name=__name__)


@router.message(
    Command("ban"),
    StaffOnlyFilter(),
    F.reply_to_message,
)
async def ban_user_handler(message: types.Message, container: Container) -> None:
    """
    Обрабатывает команду /ban для бессрочной блокировки пользователя.

    Команда должна быть ответом на сообщение нарушителя.
    Формат: /ban [причина]
    """
    dto = map_message_to_moderation_dto(message=message)

    try:
        usecase: GiveUserBanUseCase = container.resolve(GiveUserBanUseCase)
        await usecase.execute(dto=dto)
    except Exception as e:
        logger.error(f"Ошибка при бане пользователя: {e}")
        return
