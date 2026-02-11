"""Логика отмены последнего предупреждения пользователя."""

from punq import Container

from constants import Dialog
from dto import AmnestyUserDTO
from usecases.amnesty import CancelLastWarnUseCase


async def execute_cancel_warn(
    amnesty_dto: AmnestyUserDTO,
    container: Container,
) -> str:
    """Выполняет отмену последнего предупреждения.

    Args:
        amnesty_dto: Данные для амнистии.
        container: DI-контейнер.

    Returns:
        Текст сообщения об успехе.

    Raises:
        AmnestyError: При ошибке выполнения (пробрасывается из use case).
    """
    usecase = container.resolve(CancelLastWarnUseCase)
    await usecase.execute(dto=amnesty_dto)
    return Dialog.AmnestyUser.CANCEL_WARN_SUCCESS.format(
        username=amnesty_dto.violator_username
    )
