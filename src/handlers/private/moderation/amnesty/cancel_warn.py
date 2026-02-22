"""Логика отмены последнего предупреждения пользователя."""

from punq import Container

from constants import Dialog
from dto import AmnestyUserDTO
from usecases.amnesty import CancelLastWarnUseCase
from utils.moderation import format_violator_display


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
    user_display = format_violator_display(
        amnesty_dto.violator_username, amnesty_dto.violator_tgid
    )
    return Dialog.AmnestyUser.CANCEL_WARN_SUCCESS.format(user_display=user_display)
