"""Логика полной амнистии (разбан) пользователя."""

from punq import Container

from constants import Dialog
from dto import AmnestyUserDTO
from usecases.amnesty import UnbanUserUseCase
from utils.moderation import format_violator_mention_suffix


async def execute_unban(
    amnesty_dto: AmnestyUserDTO,
    container: Container,
) -> str:
    """Выполняет полную амнистию пользователя.

    Args:
        amnesty_dto: Данные для амнистии.
        container: DI-контейнер.

    Returns:
        Текст сообщения об успехе.

    Raises:
        AmnestyError: При ошибке выполнения (пробрасывается из use case).
    """
    usecase = container.resolve(UnbanUserUseCase)
    await usecase.execute(dto=amnesty_dto)
    username_display = format_violator_mention_suffix(
        amnesty_dto.violator_username, amnesty_dto.violator_tgid
    )
    return Dialog.AmnestyUser.UNBAN_SUCCESS.format(username=username_display)
