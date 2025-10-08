import logging
from typing import Optional

from aiogram import F, Router, types
from aiogram.filters import Command

from constants.punishment import PunishmentActions as Actions
from container import container
from dto import ModerationActionDTO
from filters.admin_filter import StaffOnlyFilter
from services.time_service import TimeZoneService
from usecases.moderation import GiveUserBanUseCase, GiveUserWarnUseCase

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.message(
    Command("warn"),
    StaffOnlyFilter(),
    F.reply_to_message,
)
async def warn_user_handler(message: types.Message) -> None:
    """
    Обрабатывает команду /warn для выдачи предупреждения пользователю.

    Команда должна быть ответом на сообщение нарушителя.
    Формат: /warn [причина]

    Алгоритм:
    1. Проверяет права бота и модератора
    2. Получает текущее количество наказаний пользователя
    3. Применяет наказание согласно PunishmentLadder
    4. Сохраняет запись в БД
    5. Пересылает сообщение в архивный чат
    6. Удаляет сообщение нарушителя
    7. Отправляет уведомление в чат

    Args:
        message: Сообщение с командой /warn

    Raises:
        ModerationError: При ошибках модерации (обрабатывается middleware)
    """
    dto = map_message_to_moderation_dto(message=message)
    usecase: GiveUserWarnUseCase = container.resolve(GiveUserWarnUseCase)
    await usecase.execute(dto=dto)


@router.message(
    Command("ban"),
    StaffOnlyFilter(),
    F.reply_to_message,
)
async def ban_user_handler(message: types.Message) -> None:
    """
    Обрабатывает команду /ban для бессрочной блокировки пользователя.

    Команда должна быть ответом на сообщение нарушителя.
    Формат: /ban [причина]

    Алгоритм:
    1. Проверяет права бота и модератора
    2. Банит пользователя в Telegram
    3. Обновляет статус в БД
    4. Пересылает сообщение в архивный чат
    5. Удаляет сообщение нарушителя
    6. Отправляет уведомление в чат

    Args:
        message: Сообщение с командой /ban

    Raises:
        ModerationError: При ошибках модерации (обрабатывается middleware)
    """
    dto = map_message_to_moderation_dto(message=message)
    usecase: GiveUserBanUseCase = container.resolve(GiveUserBanUseCase)
    await usecase.execute(dto=dto)


def extract_reason_from_message(message: types.Message) -> Optional[str]:
    """
    Извлекает причину наказания из текста команды.

    Args:
        message: Сообщение с командой

    Returns:
        Причина наказания или None если не указана
    """
    if not message.text:
        return None

    parts = message.text.split(maxsplit=1)
    return parts[1] if len(parts) > 1 else None


def map_message_to_moderation_dto(message: types.Message) -> ModerationActionDTO:
    """
    Преобразует Telegram сообщение в DTO для модерации.

    Извлекает все необходимые данные из сообщения:
    - Данные нарушителя (из reply_to_message)
    - Данные модератора
    - Данные чата
    - Причину наказания

    Args:
        message: Сообщение с командой модерации

    Returns:
        ModerationActionDTO с всеми необходимыми данными
    """
    reason = extract_reason_from_message(message=message)
    reply_user = message.reply_to_message.from_user

    return ModerationActionDTO(
        action=Actions.WARNING,
        user_reply_tgid=str(reply_user.id),
        user_reply_username=reply_user.username,
        admin_username=message.from_user.username,
        admin_tgid=str(message.from_user.id),
        chat_tgid=str(message.chat.id),
        chat_title=message.chat.title,
        reply_message_id=message.reply_to_message.message_id,
        original_message_id=message.message_id,
        reply_message_date=TimeZoneService.convert_to_local_time(
            dt=message.reply_to_message.date,
        ),
        original_message_date=TimeZoneService.convert_to_local_time(
            dt=message.date,
        ),
        reason=reason,
    )
