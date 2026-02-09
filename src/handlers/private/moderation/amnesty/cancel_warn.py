"""Логика отмены последнего предупреждения пользователя."""

from punq import Container

from constants import Dialog
from constants.punishment import PunishmentType
from dto import AmnestyUserDTO
from usecases.amnesty import CancelLastWarnUseCase
from utils.formatter import format_duration


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
    result = await usecase.execute(dto=amnesty_dto)

    if len(amnesty_dto.chat_dtos) == 1:
        if result.next_punishment_type == PunishmentType.BAN:
            next_step = "бессрочной блокировке."
        elif result.next_punishment_type == PunishmentType.MUTE:
            next_step = f"муту на {format_duration(result.next_punishment_duration)}"
        else:
            next_step = "предупреждению."

        return Dialog.AmnestyUser.CANCEL_WARN_SUCCESS_SINGLE.format(
            warn_count=result.current_warns_count,
            username=amnesty_dto.violator_username,
            next_step=next_step,
        )

    return Dialog.AmnestyUser.CANCEL_WARN_SUCCESS_ALL.format(
        chats_count=len(amnesty_dto.chat_dtos),
        username=amnesty_dto.violator_username,
    )
