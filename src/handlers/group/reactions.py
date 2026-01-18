import logging

from aiogram import Bot, Router, types
from punq import Container

from constants.enums import ReactionAction
from dto import MessageReactionDTO
from services.time_service import TimeZoneService
from usecases.reactions import SaveMessageReactionUseCase

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.message_reaction()
async def reaction_handler(
    event: types.MessageReactionUpdated, bot: Bot, container: Container
) -> None:
    """
    Хендлер для обработки изменений реакций на сообщениях.
    """
    # Обрабатываем только реакции от пользователей (не ботов)
    if event.user and event.user.is_bot:
        return

    await process_reaction(event, container)


async def process_reaction(
    event: types.MessageReactionUpdated,
    container: Container,
) -> None:
    """
    Сохраняет реакцию для построения метрик.
    """
    # Преобразуем время реакции в локальное время
    # В MessageReactionUpdated нет поля date, используем текущее время
    reaction_date = TimeZoneService.now()

    # Получаем идентификатор пользователя (или чата для анонимных реакций)
    user = event.user or event.actor_chat
    if not user:
        logger.warning(
            "Не удалось определить автора реакции для сообщения %s", event.message_id
        )
        return

    user_tgid = str(user.id)
    chat_tgid = str(event.chat.id)

    reaction_dto = MessageReactionDTO(
        chat_tgid=chat_tgid,
        user_tgid=user_tgid,
        message_id=str(event.message_id),
        action=_get_reaction_action(event),
        emoji=_get_emoji(event),
        message_url=_generate_message_url(event),
        created_at=reaction_date,
    )

    try:
        usecase: SaveMessageReactionUseCase = container.resolve(
            SaveMessageReactionUseCase
        )
        await usecase.execute(reaction_dto=reaction_dto)
    except Exception as e:
        logger.error("Ошибка сохранения реакции: %s", str(e), exc_info=True)


def _get_emoji(event: types.MessageReactionUpdated) -> str:
    """
    Получает эмодзи или ID кастомного эмодзи из события.
    """
    reactions = event.new_reaction or event.old_reaction
    if not reactions:
        return "Неизвестно"

    reaction = reactions[0]
    if reaction.type == "emoji":
        return reaction.emoji
    elif reaction.type == "custom_emoji":
        return reaction.custom_emoji_id

    return "Неизвестно"


def _get_reaction_action(event: types.MessageReactionUpdated) -> ReactionAction:
    """
    Определяет действие с реакцией (добавлена, удалена, изменена).
    """
    old_count = len(event.old_reaction)
    new_count = len(event.new_reaction)

    if new_count > old_count:
        return ReactionAction.ADDED
    elif new_count < old_count:
        return ReactionAction.REMOVED
    else:
        return ReactionAction.CHANGED


def _generate_message_url(event: types.MessageReactionUpdated) -> str:
    """
    Генерирует ссылку на сообщение.
    """
    chat_id = str(event.chat.id)
    message_id = event.message_id

    if chat_id.startswith("-100"):
        # Супергруппы: убираем -100
        clean_chat_id = chat_id[4:]
    elif chat_id.startswith("-"):
        # Обычные группы: убираем только -
        clean_chat_id = chat_id[1:]
    else:
        # Каналы или личные чаты
        clean_chat_id = chat_id

    return f"https://t.me/c/{clean_chat_id}/{message_id}"
