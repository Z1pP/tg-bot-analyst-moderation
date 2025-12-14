import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from constants import Dialog
from constants.callback import CallbackData
from container import container
from keyboards.inline.chats import (
    archive_bind_instruction_ikb,
    archive_channel_setting_ikb,
    chat_actions_ikb,
    chats_management_ikb,
)
from services import ChatService
from services.chat import ArchiveBindService
from services.messaging import BotMessageService
from services.permissions import BotPermissionService
from services.report_schedule_service import ReportScheduleService
from services.time_service import TimeZoneService
from services.user import UserService
from states import ChatStateManager
from utils.send_message import safe_edit_message
from utils.state_logger import log_and_set_state

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(
    F.data == CallbackData.Chat.ARCHIVE_SETTING,
)
async def archive_channel_setting_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработчик настроек архивного чата."""
    chat_id = await state.get_value("chat_id")

    try:
        chat_service: ChatService = container.resolve(ChatService)
        chat = await chat_service.get_chat_with_archive(chat_id=chat_id)
    except Exception as e:
        logger.error("Ошибка при получении чата: %s", e)
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Chat.ERROR_GET_CHAT_WITH_ARCHIVE,
            reply_markup=chats_management_ikb(),
        )
        return

    if not chat:
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Chat.CHAT_NOT_FOUND_OR_ALREADY_REMOVED,
            reply_markup=chats_management_ikb(),
        )
        return

    if chat.archive_chat:
        # Проверяем права бота в архивном чате
        bot_permission_service: BotPermissionService = container.resolve(
            BotPermissionService
        )
        permissions_check = await bot_permission_service.check_archive_permissions(
            chat_tgid=chat.archive_chat.chat_id
        )

        # Если прав недостаточно, показываем ошибку
        if not permissions_check.has_all_permissions:
            permissions_list = "\n".join(
                f"• {perm}" for perm in permissions_check.missing_permissions
            )
            error_text = Dialog.Chat.ARCHIVE_INSUFFICIENT_PERMISSIONS.format(
                title=chat.archive_chat.title, permissions_list=permissions_list
            )
            await safe_edit_message(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=error_text,
                reply_markup=archive_channel_setting_ikb(
                    archive_chat=chat.archive_chat or None,
                    invite_link=None,
                    schedule_enabled=None,
                ),
            )
            return

        # Получаем информацию о расписании рассылки
        user_service: UserService = container.resolve(UserService)
        schedule_service: ReportScheduleService = container.resolve(
            ReportScheduleService
        )

        user = await user_service.get_user(tg_id=str(callback.from_user.id))
        schedule_info = ""
        schedule_enabled = None

        if user:
            schedule = await schedule_service.get_schedule(
                user_id=user.id, chat_id=chat_id
            )

            if schedule:
                schedule_enabled = schedule.enabled
                enabled_text = "✅ Да" if schedule.enabled else "❌ Нет"
                schedule_info = f"📧 <b>Рассылка:</b> {enabled_text}\n"

                if schedule.enabled and schedule.next_run_at:
                    # Конвертируем next_run_at в локальное время для отображения
                    next_run_local = TimeZoneService.convert_to_local_time(
                        schedule.next_run_at
                    )
                    next_run_str = next_run_local.strftime("%d.%m.%Y в %H:%M")
                    schedule_info += f"⏰ <b>Следующая рассылка:</b> {next_run_str}"
                elif schedule.enabled:
                    schedule_info += "⏰ <b>Следующая рассылка:</b> не запланирована"
            else:
                schedule_info = (
                    "📧 <b>Рассылка:</b> ❌ Нет\n"
                    "⏰ <b>Следующая рассылка:</b> не настроена"
                )

        text = Dialog.Chat.ARCHIVE_CHANNEL_EXISTS.format(
            title=chat.title, schedule_info=schedule_info
        )

        # Получаем invite ссылку через API только если все права есть
        bot_message_service: BotMessageService = container.resolve(BotMessageService)
        invite_link = await bot_message_service.get_chat_invite_link(
            chat_tgid=chat.archive_chat.chat_id
        )
    else:
        text = Dialog.Chat.ARCHIVE_CHANNEL_MISSING.format(title=chat.title)
        invite_link = None
        schedule_enabled = None

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=text,
        reply_markup=archive_channel_setting_ikb(
            archive_chat=chat.archive_chat or None,
            invite_link=invite_link,
            schedule_enabled=schedule_enabled,
        ),
    )


@router.callback_query(
    F.data == CallbackData.Chat.ARCHIVE_TOGGLE_SCHEDULE,
)
async def archive_toggle_schedule_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработчик переключения рассылки."""
    await callback.answer()

    chat_id = await state.get_value("chat_id")

    if not chat_id:
        logger.error("chat_id не найден в state")
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Chat.ERROR_GET_CHAT_WITH_ARCHIVE,
            reply_markup=chats_management_ikb(),
        )
        return

    try:
        # Получаем пользователя и расписание
        user_service: UserService = container.resolve(UserService)
        schedule_service: ReportScheduleService = container.resolve(
            ReportScheduleService
        )
        chat_service: ChatService = container.resolve(ChatService)

        user = await user_service.get_user(tg_id=str(callback.from_user.id))
        if not user:
            logger.error("Пользователь не найден: tg_id=%s", callback.from_user.id)
            await callback.answer("❌ Ошибка: пользователь не найден", show_alert=True)
            return

        schedule = await schedule_service.get_schedule(user_id=user.id, chat_id=chat_id)

        if not schedule:
            await callback.answer(
                "❌ Расписание не найдено. Сначала настройте время отправки.",
                show_alert=True,
            )
            return

        # Переключаем рассылку
        new_enabled = not schedule.enabled
        updated_schedule = await schedule_service.toggle_schedule(
            user_id=user.id, chat_id=chat_id, enabled=new_enabled
        )

        if not updated_schedule:
            await callback.answer(
                "❌ Ошибка при обновлении расписания", show_alert=True
            )
            return

        # Обновляем сообщение с новой информацией
        chat = await chat_service.get_chat_with_archive(chat_id=chat_id)
        if not chat or not chat.archive_chat:
            await callback.answer("❌ Чат не найден", show_alert=True)
            return

        # Формируем информацию о расписании
        schedule_info = ""
        schedule_enabled = updated_schedule.enabled
        enabled_text = "✅ Да" if schedule_enabled else "❌ Нет"
        schedule_info = f"📧 <b>Рассылка:</b> {enabled_text}\n"

        if schedule_enabled and updated_schedule.next_run_at:
            next_run_local = TimeZoneService.convert_to_local_time(
                updated_schedule.next_run_at
            )
            next_run_str = next_run_local.strftime("%d.%m.%Y в %H:%M")
            schedule_info += f"⏰ <b>Следующая рассылка:</b> {next_run_str}"
        elif schedule_enabled:
            schedule_info += "⏰ <b>Следующая рассылка:</b> не запланирована"

        text = Dialog.Chat.ARCHIVE_CHANNEL_EXISTS.format(
            title=chat.title, schedule_info=schedule_info
        )

        # Получаем invite ссылку
        bot_message_service: BotMessageService = container.resolve(BotMessageService)
        invite_link = await bot_message_service.get_chat_invite_link(
            chat_tgid=chat.archive_chat.chat_id
        )

        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=text,
            reply_markup=archive_channel_setting_ikb(
                archive_chat=chat.archive_chat or None,
                invite_link=invite_link,
                schedule_enabled=schedule_enabled,
            ),
        )

    except Exception as e:
        logger.error("Ошибка при переключении рассылки: %s", e, exc_info=True)
        await callback.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(
    F.data == CallbackData.Chat.ARCHIVE_BIND_INSTRUCTION,
)
async def archive_bind_instruction_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработчик инструкции по привязке архивного канала."""
    chat_id = await state.get_value("chat_id")

    if not chat_id:
        logger.error("chat_id не найден в state")
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Chat.ERROR_GET_CHAT_WITH_ARCHIVE,
            reply_markup=chats_management_ikb(),
        )
        return

    try:
        # Генерируем hash для привязки
        archive_bind_service: ArchiveBindService = container.resolve(ArchiveBindService)
        bind_hash = archive_bind_service.generate_bind_hash(chat_id=chat_id)

        # Формируем текст инструкции с hash
        instruction_text = (
            f"{Dialog.Chat.ARCHIVE_BIND_INSTRUCTION}\n\n"
            f"🔑 <b>Ваш код привязки:</b>\n"
            f"<code>{bind_hash}</code>\n\n"
            f"Отправьте этот код в архивном чате для привязки."
        )

        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=instruction_text,
            reply_markup=archive_bind_instruction_ikb(),
        )
    except Exception as e:
        logger.error("Ошибка при генерации hash для привязки: %s", e)
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Chat.ARCHIVE_BIND_INSTRUCTION,
            reply_markup=archive_bind_instruction_ikb(),
        )


@router.callback_query(
    F.data == CallbackData.Chat.BACK_TO_CHAT_ACTIONS,
    ChatStateManager.selecting_chat,
)
async def archive_back_to_chat_actions_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработчик возврата к меню действий чата из архива."""
    await callback.answer()

    chat_id = await state.get_value("chat_id")

    try:
        chat_service: ChatService = container.resolve(ChatService)
        chat = await chat_service.get_chat_with_archive(chat_id=chat_id)
    except Exception as e:
        logger.error("Ошибка при получении чата: %s", e)
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Chat.ERROR_GET_CHAT_WITH_ARCHIVE,
            reply_markup=chats_management_ikb(),
        )
        return

    if not chat:
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Chat.CHAT_NOT_FOUND_OR_ALREADY_REMOVED,
            reply_markup=chats_management_ikb(),
        )
        return

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Chat.CHAT_ACTIONS.format(title=chat.title),
        reply_markup=chat_actions_ikb(),
    )

    await log_and_set_state(
        message=callback.message,
        state=state,
        new_state=ChatStateManager.selecting_chat,
    )
