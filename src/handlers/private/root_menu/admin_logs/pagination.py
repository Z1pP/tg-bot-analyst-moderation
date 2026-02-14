import logging
from typing import Optional

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from punq import Container

from constants import Dialog
from constants.pagination import DEFAULT_PAGE_SIZE
from dto.admin_log import GetAdminLogsPageDTO
from exceptions import AdminLogsError
from keyboards.inline.admin_logs import admin_logs_ikb
from usecases.admin_logs import GetAdminLogsPageUseCase
from utils.send_message import safe_edit_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)


def _parse_pagination_callback(callback_data: str) -> tuple[int, Optional[int]]:
    """Парсит callback_data: prev/next_admin_logs_page__{page} или __{page}__{admin_id}."""
    parts = callback_data.split("__")
    current_page = int(parts[1])
    admin_id: Optional[int] = (
        int(parts[2]) if len(parts) > 2 and parts[2] != "None" else None
    )
    return current_page, admin_id


@router.callback_query(F.data.startswith("prev_admin_logs_page__"))
async def prev_admin_logs_page_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    """Обработчик перехода на предыдущую страницу логов."""
    await callback.answer()
    if callback.data is None or callback.message is None:
        return
    if not isinstance(callback.message, types.Message):
        return

    try:
        current_page, admin_id = _parse_pagination_callback(callback.data)
        prev_page = max(1, current_page - 1)

        dto = GetAdminLogsPageDTO(
            admin_id=admin_id,
            page=prev_page,
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
                page=prev_page,
                total_count=result.total_count,
                page_size=DEFAULT_PAGE_SIZE,
                admin_id=admin_id,
            ),
        )
    except AdminLogsError as e:
        await callback.answer(e.get_user_message(), show_alert=True)
    except Exception as e:
        logger.error(
            "Ошибка при переходе на предыдущую страницу логов: %s", e, exc_info=True
        )
        await callback.answer(Dialog.AdminLogs.ERROR_LOAD_PAGE, show_alert=True)


@router.callback_query(F.data.startswith("next_admin_logs_page__"))
async def next_admin_logs_page_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    """Обработчик перехода на следующую страницу логов."""
    await callback.answer()
    if callback.data is None or callback.message is None:
        return
    if not isinstance(callback.message, types.Message):
        return

    try:
        current_page, admin_id = _parse_pagination_callback(callback.data)
        next_page = current_page + 1

        dto = GetAdminLogsPageDTO(
            admin_id=admin_id,
            page=next_page,
            limit=DEFAULT_PAGE_SIZE,
        )
        usecase: GetAdminLogsPageUseCase = container.resolve(GetAdminLogsPageUseCase)
        result = await usecase.execute(dto)

        if not result.entry_lines:
            await callback.answer(Dialog.AdminLogs.LAST_PAGE, show_alert=True)
            return

        text = result.header_text + "\n" + "\n".join(result.entry_lines)

        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=text,
            reply_markup=admin_logs_ikb(
                page=next_page,
                total_count=result.total_count,
                page_size=DEFAULT_PAGE_SIZE,
                admin_id=admin_id,
            ),
        )
    except AdminLogsError as e:
        await callback.answer(e.get_user_message(), show_alert=True)
    except Exception as e:
        logger.error(
            "Ошибка при переходе на следующую страницу логов: %s", e, exc_info=True
        )
        await callback.answer(Dialog.AdminLogs.ERROR_LOAD_PAGE, show_alert=True)


@router.callback_query(F.data == "admin_logs_page_info")
async def admin_logs_page_info_handler(
    callback: types.CallbackQuery, state: FSMContext
) -> None:
    """Обработчик информации о странице (не делает ничего, просто отвечает)."""
    await callback.answer()
