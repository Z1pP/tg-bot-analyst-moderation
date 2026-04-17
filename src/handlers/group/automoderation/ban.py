"""Колбэк «Заблокировать» на карточке авто-модерации: полный сценарий бана через GiveUserBanUseCase."""

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from punq import Container

from constants.callback import CallbackData
from constants.enums import ChatType
from constants.punishment import PunishmentActions as Actions
from dto import ModerationActionDTO
from services import ChatService
from services.permissions.bot_permission import BotPermissionService
from usecases.moderation import GiveUserBanUseCase
from utils.automoderation_callback import decode_automod_block_callback
from utils.parse_automoderation_card import parse_automoderation_card

from .staff import is_automoderation_staff

logger = logging.getLogger(__name__)
router = Router(name=__name__)


@router.callback_query(
    F.data.startswith(CallbackData.AutoModeration.BLOCK_PREFIX),
    F.message.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP]),
)
async def automoderation_block_user_handler(
    callback: CallbackQuery,
    container: Container,
    state: FSMContext,
) -> None:
    """Бан нарушителя в рабочем чате по данным карточки (как при команде /ban)."""
    if not await is_automoderation_staff(callback, container):
        await callback.answer(
            "\u26d4 Недостаточно прав для этого действия.",
            show_alert=True,
        )
        return

    work_chat_tgid, violator_id = decode_automod_block_callback(callback.data or "")
    if not work_chat_tgid or violator_id is None:
        logger.warning("automod block: битый callback %r", callback.data)
        await callback.answer("Некорректные данные кнопки.", show_alert=True)
        return

    if not callback.message:
        await callback.answer("Сообщение недоступно.", show_alert=True)
        return

    chat_service: ChatService = container.resolve(ChatService)
    chat = await chat_service.get_chat_with_archive(chat_tgid=work_chat_tgid)
    if not chat or not chat.archive_chat_id:
        await callback.answer(
            "Чат не найден или не привязан архив.",
            show_alert=True,
        )
        return
    if str(chat.archive_chat_id) != str(callback.message.chat.id):
        await callback.answer(
            "Карточка не из архива этого чата.",
            show_alert=True,
        )
        return

    html_text = getattr(callback.message, "html_text", None)
    parsed = parse_automoderation_card(
        text=callback.message.text,
        html_text=html_text,
    )
    if parsed.reply_message_id is None:
        await callback.answer(
            "Не удалось определить сообщение нарушителя по карточке.",
            show_alert=True,
        )
        return

    permission_service: BotPermissionService = container.resolve(BotPermissionService)
    violator_username = await permission_service.get_member_username(
        user_id=violator_id,
        chat_tgid=work_chat_tgid,
    )
    if not violator_username and parsed.violator_username_hint:
        violator_username = parsed.violator_username_hint

    dto = ModerationActionDTO(
        action=Actions.BAN,
        violator_tgid=str(violator_id),
        violator_username=violator_username,
        admin_username=callback.from_user.username or "",
        admin_tgid=str(callback.from_user.id),
        chat_tgid=work_chat_tgid,
        chat_title=chat.title or "",
        reply_message_id=parsed.reply_message_id,
        reason=parsed.reason,
        from_admin_panel=False,
        from_auto_moderation=True,
    )

    usecase: GiveUserBanUseCase = container.resolve(GiveUserBanUseCase)
    try:
        ok = await usecase.execute(dto=dto)
    except Exception:
        logger.exception(
            "automod block: ошибка GiveUserBan work_chat=%s user=%s",
            work_chat_tgid,
            violator_id,
        )
        await callback.answer("Ошибка при блокировке.", show_alert=True)
        return

    if ok:
        await state.clear()
        await callback.answer("Пользователь заблокирован.")
        try:
            await callback.message.delete()
        except Exception as e:
            logger.warning("automod block: не удалось удалить карточку: %s", e)
    else:
        await callback.answer(
            "Не удалось выполнить блокировку. Проверьте личные сообщения от бота.",
            show_alert=True,
        )
