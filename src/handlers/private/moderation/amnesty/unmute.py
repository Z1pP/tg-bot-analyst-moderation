"""Логика размута пользователя."""

from punq import Container

from constants import Dialog
from dto import AmnestyUserDTO
from usecases.amnesty import UnmuteUserUseCase
from utils.moderation import format_violator_mention_suffix


async def execute_unmute(
    amnesty_dto: AmnestyUserDTO,
    container: Container,
) -> str:
    """Выполняет размут пользователя.

    Args:
        amnesty_dto: Данные для амнистии.
        container: DI-контейнер.

    Returns:
        Текст сообщения об успехе.

    Raises:
        AmnestyError: При ошибке выполнения (пробрасывается из use case).
    """
    usecase = container.resolve(UnmuteUserUseCase)
    await usecase.execute(dto=amnesty_dto)
    username_display = format_violator_mention_suffix(
        amnesty_dto.violator_username, amnesty_dto.violator_tgid
    )
    return Dialog.AmnestyUser.UNMUTE_SUCCESS.format(username=username_display)
