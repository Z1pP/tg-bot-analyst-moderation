import logging

from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message
from punq import Container

from filters.admin_filter import AdminOnlyFilter
from filters.group_filter import GroupTypeFilter
from models import ChatSession, User
from services.chat import ChatService
from services.user import UserService
from usecases.chat_tracking import AddChatToTrackUseCase, RemoveChatFromTrackingUseCase

logger = logging.getLogger(__name__)
router = Router(name=__name__)


@router.message(Command("track"), GroupTypeFilter(), AdminOnlyFilter())
async def chat_added_to_tracking_handler(
    message: Message, container: Container
) -> None:
    """Обработчик команды /track для добавления чата в отслеживание."""

    logger.info(
        f"Получена команда /track от {message.from_user.username} "
        f"в чате '{message.chat.title}' (ID: {message.chat.id})"
    )

    admin, chat = await _get_admin_and_chat(message=message, container=container)

    if not admin or not chat:
        logger.error("Не удалось получить данные о пользователе или чате")
        return

    try:
        logger.info(f"Проверка прав бота в чате '{chat.title}' (ID: {chat.chat_id})")

        bot_status = await check_bot_permissions(
            bot=message.bot,
            chat_id=chat.chat_id,
        )

        if not bot_status["is_admin"]:
            logger.warning(
                f"Недостаточно прав бота в чате '{chat.title}'. "
                f"Статус: {bot_status['status']}"
            )
            await send_permission_error(message, admin, chat, bot_status)
            await message.delete()
            return

        logger.info(f"Права бота проверены успешно. Статус: {bot_status['status']}")

        # Добавляем чат в отслеживание
        usecase: AddChatToTrackUseCase = container.resolve(AddChatToTrackUseCase)
        _, is_exists = await usecase.execute(chat=chat, admin=admin)

        if is_exists:
            await send_already_tracked_notification(
                message=message,
                admin=admin,
                chat=chat,
            )
            return

        logger.info(
            f"Чат '{chat.title}' успешно добавлен "
            f"в отслеживание админом {admin.username}"
        )

        await send_admin_notification(
            message=message,
            admin=admin,
            chat=chat,
        )
    except Exception as e:
        logger.error(f"Ошибка при обработке команды /track: {e}", exc_info=True)
    finally:
        await message.delete()


@router.message(Command("untrack"), GroupTypeFilter(), AdminOnlyFilter())
async def chat_removed_from_tracking_handler(
    message: Message, container: Container
) -> None:
    """Обработчик команды /untrack для удаления чата из отслеживания."""

    logger.info(
        f"Получена команда /untrack от {message.from_user.username} "
        f"в чате '{message.chat.title}' (ID: {message.chat.id})"
    )

    admin, chat = await _get_admin_and_chat(message=message, container=container)

    if not admin or not chat:
        logger.error("Не удалось получить данные о пользователе или чате")
        return

    try:
        usecase: RemoveChatFromTrackingUseCase = container.resolve(
            RemoveChatFromTrackingUseCase
        )

        success, _ = await usecase.execute(user_id=admin.id, chat_id=chat.id)

        if success:
            logger.info(
                f"Чат '{chat.title}' успешно удален "
                f"из отслеживания админом {admin.username}"
            )

            notification_text = (
                "✅ <b>Чат удален из отслеживания</b>\n\n"
                f"📋 <b>Название:</b> {chat.title}\n"
                f"🆔 <b>ID чата:</b> <code>{chat.chat_id}</code>\n"
                f"👤 <b>Удалил:</b> @{admin.username}\n\n"
                "❗️Вы всегда можете вернуть чат в отслеживаемые "
                "и продолжить собирать статистику"
            )
        else:
            logger.warning(f"Чат '{chat.title}' не найден в отслеживании")

            notification_text = (
                "ℹ️ <b>Чат не отслеживается</b>\n\n"
                f"📋 <b>Название:</b> {chat.title}\n"
                f"🆔 <b>ID чата:</b> <code>{chat.chat_id}</code>\n\n"
                "Этот чат не находится в списке отслеживания."
            )

        await send_notification(
            bot=message.bot,
            chat_id=message.from_user.id,
            message_text=notification_text,
        )

    except Exception as e:
        logger.error(f"Ошибка при обработке команды /untrack: {e}", exc_info=True)
    finally:
        await message.delete()


async def send_permission_error(
    message: Message, admin: User, chat: ChatSession, bot_status: dict
) -> None:
    """Отправляет сообщение об ошибке прав в приватный чат"""
    try:
        admin_telegram_id = message.from_user.id

        logger.debug(
            "Отправка уведомления об ошибке "
            "прав админу {admin.username} (ID: {admin_telegram_id})"
        )

        if not bot_status["is_member"]:
            error_text = (
                "❌ <b>Ошибка добавления чата</b>\n\n"
                f"📋 <b>Чат:</b> {chat.title}\n"
                f"🆔 <b>ID:</b> <code>{chat.chat_id}</code>\n\n"
                f"⚠️ <b>Проблема:</b> Бот не добавлен в чат\n\n"
                f"<b>Решение:</b>\n"
                f"1. Добавьте бота в чат\n"
                f"2. Повторите команду /track"
            )
        else:
            error_text = (
                "❌ <b>Ошибка добавления чата</b>\n\n"
                f"📋 <b>Чат:</b> {chat.title}\n"
                f"🆔 <b>ID:</b> <code>{chat.chat_id}</code>\n\n"
                f"⚠️ <b>Проблема:</b> Недостаточно прав\n"
                f"🤖 <b>Статус бота:</b> {bot_status['status']}\n\n"
                f"<b>Решение:</b>\n"
                f"1. Дайте боту права администратора\n"
                f"2. Включите права:\n"
                f"   • Чтение всех сообщений\n"
                f"   • Удаление сообщений\n"
                f"3. Повторите команду /track"
            )

        await message.bot.send_message(
            chat_id=admin_telegram_id,
            text=error_text,
            parse_mode="HTML",
        )

        logger.info(f"Уведомление об ошибке прав отправлено админу {admin.username}")

    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления об ошибке: {e}")


async def send_already_tracked_notification(
    message: Message,
    admin: User,
    chat: ChatSession,
) -> None:
    try:
        logger.debug(
            f"Отправка уведомления админу {admin.username} что чат уже отслеживается"
        )

        notification_text = (
            "ℹ️ <b>Чат уже отслеживается</b>\n\n"
            f"📋 <b>Название:</b> {chat.title}\n"
            f"🆔 <b>ID чата:</b> <code>{chat.chat_id}</code>\n\n"
            f"Этот чат уже добавлен в ваш список отслеживания.\n"
            f"Повторное добавление не требуется."
        )

        await send_notification(
            bot=message.bot,
            chat_id=message.from_user.id,
            message_text=notification_text,
        )

        logger.info(f"Уведомление отправлено админу {admin.username}")
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления что чат уже отслеживается: {e}")


async def send_admin_notification(
    message: Message,
    admin: User,
    chat: ChatSession,
) -> None:
    try:
        logger.debug(
            "Отправка уведомления об успехе "
            f"админу {admin.username} (ID: {message.from_user.id})"
        )

        notification_text = (
            "✅ <b>Чат успешно добавлен в отслеживание</b>\n\n"
            f"📋 <b>Название:</b> {chat.title}\n"
            f"🆔 <b>ID чата:</b> <code>{chat.chat_id}</code>\n"
            f"👤 <b>Добавил:</b> @{admin.username}"
        )

        await send_notification(
            bot=message.bot,
            chat_id=message.from_user.id,
            message_text=notification_text,
        )

        logger.info(
            f"Уведомление об успешном добавлении отправлено админу {admin.username}"
        )

    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления об успехе: {e}")


async def send_notification(
    bot: Bot,
    chat_id: int,
    message_text: str,
    parse_mode: str = "HTML",
) -> None:
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=message_text,
            parse_mode=parse_mode,
        )
        logger.info(f"Отправлено сообщения в чат с chat_id={chat_id}")
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления в чат с chat_id={chat_id}: {e}")


async def check_bot_permissions(bot: Bot, chat_id: str) -> dict:
    try:
        logger.debug(f"Проверка прав бота в чате {chat_id}")

        # Получаем информацию о боте в чате
        bot_member = await bot.get_chat_member(chat_id=chat_id, user_id=bot.id)

        is_member = bot_member.status in ["member", "administrator", "creator"]
        is_admin = bot_member.status in ["administrator", "creator"]

        permissions = {}
        if hasattr(bot_member, "can_read_all_group_messages"):
            permissions = {
                "can_read_messages": getattr(
                    bot_member, "can_read_all_group_messages", False
                ),
                "can_delete_messages": getattr(
                    bot_member, "can_delete_messages", False
                ),
                "can_restrict_members": getattr(
                    bot_member, "can_restrict_members", False
                ),
            }

        result = {
            "is_member": is_member,
            "is_admin": is_admin,
            "status": bot_member.status,
            "permissions": permissions,
        }

        logger.debug(
            f"Статус бота в чате {chat_id}: {bot_member.status}, админ: {is_admin}"
        )

        return result

    except Exception as e:
        logger.warning(f"Не удалось получить информацию о боте в чате {chat_id}: {e}")
        # Если бот не может получить информацию, значит его нет в чате
        return {
            "is_member": False,
            "is_admin": False,
            "status": "not_member",
            "permissions": {},
        }


async def _get_admin_and_chat(
    message: Message, container: Container
) -> tuple[User, ChatSession]:
    """Получает пользователя и чат из сообщения."""

    logger.debug(f"Получение данных админа и чата для {message.from_user.username}")

    # Получаем сервисы
    user_service: UserService = container.resolve(UserService)
    chat_service: ChatService = container.resolve(ChatService)

    # Получаем пользователя и чат
    user_tg_id = str(message.from_user.id)
    chat_id = str(message.chat.id)

    if not user_tg_id:
        logger.warning("Пользователь без tg_id: %s", message.from_user.id)
        return None, None

    admin = await user_service.get_user(user_tg_id)
    if not admin:
        logger.warning("Пользователь не найден в базе данных: %s", user_tg_id)
        return None, None

    chat = await chat_service.get_or_create(
        chat_tgid=chat_id, title=message.chat.title or "Без названия"
    )
    if not chat:
        logger.error("Не удалось получить или создать чат: %s", chat_id)
        return None, None

    logger.debug(f"Данные получены: админ {admin.username}, чат '{chat.title}'")
    return admin, chat
