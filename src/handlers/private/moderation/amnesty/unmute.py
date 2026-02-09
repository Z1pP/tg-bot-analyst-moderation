"""Логика размута пользователя."""

from punq import Container

from constants import Dialog
from dto import AmnestyUserDTO
from usecases.amnesty import UnmuteUserUseCase


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
    return Dialog.AmnestyUser.UNMUTE_SUCCESS.format(
        username=amnesty_dto.violator_username
    )
