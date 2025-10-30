import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from container import container
from dto.message_action import MessageActionDTO
from exceptions.moderation import MessageDeleteError
from states.message_management import MessageManagerState
from usecases.admin_actions import DeleteMessageUseCase

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(
    MessageManagerState.waiting_delete_confirm,
    F.data.in_(["delete_message_confirm", "delete_message_cancel"]),
)
async def message_delete_confirm_handler(
    callback: types.CallbackQuery, state: FSMContext
) -> None:
    """Обработчик подтверждения удаления сообщения."""
    await callback.answer()

    if callback.data == "delete_message_cancel":
        await callback.message.edit_text("❌ Удаление отменено")
        await state.clear()
        logger.info("Админ %s отменил удаление", callback.from_user.id)
        return

    data = await state.get_data()
    chat_tgid = data.get("chat_tgid")
    message_id = data.get("message_id")

    if not chat_tgid or not message_id:
        logger.error("Некорректные данные в state: %s", data)
        await callback.message.edit_text("❌ Ошибка: некорректные данные")
        await state.clear()
        return

    dto = MessageActionDTO(
        chat_tgid=chat_tgid,
        message_id=message_id,
        admin_tgid=str(callback.from_user.id),
        admin_username=callback.from_user.username or "unknown",
    )

    usecase: DeleteMessageUseCase = container.resolve(DeleteMessageUseCase)

    try:
        await usecase.execute(dto)
        await callback.message.edit_text("✅ Сообщение успешно удалено")
        logger.info(
            "Админ %s удалил сообщение %s из чата %s",
            callback.from_user.id,
            message_id,
            chat_tgid,
        )
    except MessageDeleteError as e:
        await callback.message.edit_text(e.get_user_message())
    except Exception as e:
        logger.error(
            "Ошибка удаления сообщения %s: %s",
            message_id,
            e,
            exc_info=True,
        )
        await callback.message.edit_text("❌ Непредвиденная ошибка удаления сообщения")

    await state.clear()
