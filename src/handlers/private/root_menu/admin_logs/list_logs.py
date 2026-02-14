import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from constants.pagination import DEFAULT_PAGE_SIZE
from dto.admin_log import GetAdminLogsPageDTO
from exceptions import AdminLogsError
from keyboards.inline.admin_logs import admin_logs_ikb, admin_select_ikb
from keyboards.inline.menu import main_menu_ikb
from usecases.admin_logs import GetAdminLogsPageUseCase, GetAdminsWithLogsUseCase
from utils.send_message import safe_edit_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data == CallbackData.AdminLogs.SHOW_MENU)
async def admin_logs_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    container: Container,
    user_language: str,
) -> None:
    """Обработчик просмотра логов действий администраторов - показывает список администраторов."""
    await callback.answer()
    if callback.message is None or not isinstance(callback.message, types.Message):
        return

    try:
        usecase: GetAdminsWithLogsUseCase = container.resolve(GetAdminsWithLogsUseCase)
        admins = await usecase.execute()

        if not admins:
            text = f"{Dialog.AdminLogs.ADMIN_LOGS_TITLE}\n\n{Dialog.AdminLogs.NO_LOGS}"
        else:
            text = Dialog.AdminLogs.SELECT_ADMIN

        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=text,
            reply_markup=admin_select_ikb(admins),
        )

    except AdminLogsError as e:
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=e.get_user_message(),
            reply_markup=main_menu_ikb(
                user=None,
                user_language=user_language,
                admin_tg_id=str(callback.from_user.id),
            ),
        )
    except Exception as e:
        logger.error(
            "Ошибка при получении списка администраторов: %s", e, exc_info=True
        )

        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.AdminLogs.ERROR_GET_ADMINS,
            reply_markup=main_menu_ikb(
                user=None,
                user_language=user_language,
                admin_tg_id=str(callback.from_user.id),
            ),
        )


@router.callback_query(lambda c: c.data.startswith("admin_logs__"))
async def admin_logs_select_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    """Обработчик выбора администратора для просмотра логов."""
    await callback.answer()
    if callback.data is None or callback.message is None:
        return
    if not isinstance(callback.message, types.Message):
        return

    try:
        parts = callback.data.split("__")
        admin_id_str = parts[1] if len(parts) > 1 else None
        admin_id: int | None = (
            None
            if (admin_id_str is None or admin_id_str == "all")
            else int(admin_id_str)
        )

        dto = GetAdminLogsPageDTO(
            admin_id=admin_id,
            page=1,
            limit=DEFAULT_PAGE_SIZE,
        )
        usecase: GetAdminLogsPageUseCase = container.resolve(GetAdminLogsPageUseCase)
        result = await usecase.execute(dto)

        if not result.entry_lines:
            text = f"{result.header_text}\n{Dialog.AdminLogs.NO_LOGS}"
        else:
            text = result.header_text + "\n" + "\n".join(result.entry_lines)

        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=text,
            reply_markup=admin_logs_ikb(
                page=1,
                total_count=result.total_count,
                page_size=DEFAULT_PAGE_SIZE,
                admin_id=admin_id,
            ),
        )

    except AdminLogsError as e:
        await callback.answer(e.get_user_message(), show_alert=True)
    except Exception as e:
        logger.error("Ошибка при получении логов администратора: %s", e, exc_info=True)
        await callback.answer(Dialog.AdminLogs.ERROR_GET_LOGS, show_alert=True)
