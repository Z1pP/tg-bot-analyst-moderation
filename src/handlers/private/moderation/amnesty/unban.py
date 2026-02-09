"""Логика полной амнистии (разбан) пользователя."""

from punq import Container

from constants import Dialog
from dto import AmnestyUserDTO
from usecases.amnesty import UnbanUserUseCase


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
    return Dialog.AmnestyUser.UNBAN_SUCCESS.format(
        username=amnesty_dto.violator_username
    )
