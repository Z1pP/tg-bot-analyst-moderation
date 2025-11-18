import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from constants.callback import CallbackData
from constants.enums import UserRole
from container import container
from keyboards.inline.users import role_select_ikb
from repositories import UserRepository
from services.caching import ICache
from services.user import UserService
from utils.user_data_parser import parse_data_from_text

router = Router(name=__name__)
logger = logging.getLogger(__name__)

# Защищенный пользователь - нельзя изменить роль
PROTECTED_TG_ID = "879565689"


@router.message(Command("role"))
async def role_command_handler(message: Message) -> None:
    """
    Обработчик команды /role для изменения роли пользователя.
    Формат: /role @username или /role tg_id
    """
    try:
        # Удаляем исходное сообщение с командой
        try:
            await message.delete()
        except Exception as e:
            logger.warning("Не удалось удалить сообщение с командой /role: %s", e)

        # Парсим аргументы команды
        if not message.text:
            await message.answer(
                "❌ Не указан пользователь. Используйте: /role @username или /role tg_id"
            )
            return

        # Разделяем команду и аргументы
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            await message.answer(
                "❌ Не указан пользователь. Используйте: /role @username или /role tg_id"
            )
            return

        user_input = parts[1].strip()
        user_data = parse_data_from_text(text=user_input)

        if user_data is None:
            await message.answer(
                "❌ Неверный формат. Используйте: /role @username или /role tg_id"
            )
            return

        # Находим пользователя
        user_service: UserService = container.resolve(UserService)
        user = None

        if user_data.tg_id:
            user = await user_service.get_user(tg_id=user_data.tg_id)
        elif user_data.username:
            user = await user_service.get_by_username(username=user_data.username)

        if not user:
            await message.answer(
                f"❌ Пользователь не найден.\n"
                f"Проверьте правильность введенных данных: {user_input}"
            )
            return

        # Защита от изменения роли для захардкоженного пользователя
        if user.tg_id == PROTECTED_TG_ID:
            await message.answer("❌ Нельзя изменить роль этому пользователю")
            return

        # Формируем текст сообщения
        username_display = user.username if user.username else f"ID:{user.tg_id}"
        role_display = {
            UserRole.ADMIN: "👑 Администратор",
            UserRole.MODERATOR: "🛡️ Модератор",
            UserRole.USER: "👤 Пользователь",
        }.get(user.role, "❓ Неизвестно")

        text = (
            f"🔧 <b>Изменение роли пользователя</b>\n\n"
            f"👤 Пользователь: @{username_display}\n"
            f"📋 Текущая роль: {role_display}\n\n"
            f"Выберите новую роль:"
        )

        # Показываем клавиатуру выбора роли
        await message.answer(
            text=text,
            reply_markup=role_select_ikb(user_id=user.id, current_role=user.role),
        )

        logger.info(
            f"Админ {message.from_user.id} запросил изменение роли для пользователя {user.id} ({username_display})"
        )

    except Exception as e:
        logger.error(f"Ошибка при обработке команды /role: {e}", exc_info=True)
        await message.answer("❌ Произошла ошибка при обработке команды")


@router.callback_query(F.data.startswith(CallbackData.User.PREFIX_ROLE_SELECT))
async def role_select_callback_handler(callback: CallbackQuery) -> None:
    """
    Обработчик выбора роли из inline клавиатуры.
    Формат callback_data: role_select__{user_id}__{role}
    """
    await callback.answer()

    try:
        # Проверяем права администратора
        admin_tg_id = str(callback.from_user.id)
        user_service: UserService = container.resolve(UserService)
        admin_user = await user_service.get_user(tg_id=admin_tg_id)

        if not admin_user or admin_user.role != UserRole.ADMIN:
            await callback.answer(
                "❌ У вас нет прав для выполнения этого действия", show_alert=True
            )
            return
        # Парсим callback_data
        callback_data = callback.data.replace(CallbackData.User.PREFIX_ROLE_SELECT, "")
        parts = callback_data.split("__")

        if len(parts) != 2:
            logger.error(f"Неверный формат callback_data: {callback.data}")
            await callback.message.edit_text("❌ Ошибка: неверный формат данных")
            return

        user_id_str, role_str = parts
        user_id = int(user_id_str)

        # Валидируем роль
        try:
            new_role = UserRole(role_str)
        except ValueError:
            logger.error(f"Неверная роль: {role_str}")
            await callback.message.edit_text(f"❌ Ошибка: неверная роль '{role_str}'")
            return

        # Получаем пользователя
        user_repo: UserRepository = container.resolve(UserRepository)
        user = await user_repo.get_user_by_id(user_id=user_id)

        if not user:
            await callback.message.edit_text("❌ Пользователь не найден")
            return

        # Защита от изменения роли для захардкоженного пользователя
        if user.tg_id == PROTECTED_TG_ID:
            await callback.message.edit_text(
                "❌ Нельзя изменить роль этому пользователю"
            )
            await callback.answer(
                "❌ Этот пользователь защищен от изменения роли", show_alert=True
            )
            return

        old_role = user.role

        # Если роль не изменилась, просто обновляем сообщение
        if old_role == new_role:
            username_display = user.username if user.username else f"ID:{user.tg_id}"
            role_display = {
                UserRole.ADMIN: "👑 Администратор",
                UserRole.MODERATOR: "🛡️ Модератор",
                UserRole.USER: "👤 Пользователь",
            }.get(new_role, "❓ Неизвестно")

            text = (
                f"🔧 <b>Изменение роли пользователя</b>\n\n"
                f"👤 Пользователь: @{username_display}\n"
                f"📋 Текущая роль: {role_display}\n\n"
                f"✅ Роль уже установлена на {role_display}"
            )

            await callback.message.edit_text(
                text=text,
                reply_markup=role_select_ikb(user_id=user.id, current_role=new_role),
            )
            return

        # Обновляем роль
        updated_user = await user_repo.update_user_role(
            user_id=user_id, new_role=new_role
        )

        if not updated_user:
            await callback.message.edit_text("❌ Не удалось обновить роль пользователя")
            return

        # Инвалидируем и обновляем кеш
        # Важно: используем те же ключи, что и в BaseUserFilter и UserService
        cache: ICache = container.resolve(ICache)
        if updated_user.tg_id:
            # Удаляем старые значения из кеша
            await cache.delete(updated_user.tg_id)  # Ключ для BaseUserFilter
            await cache.delete(
                f"user:tg_id:{updated_user.tg_id}"
            )  # Ключ для UserService
            # Обновляем кеш с новой ролью
            await cache.set(updated_user.tg_id, updated_user)  # Ключ для BaseUserFilter
            await cache.set(
                f"user:tg_id:{updated_user.tg_id}", updated_user
            )  # Ключ для UserService
        if updated_user.username:
            await cache.delete(f"user:username:{updated_user.username}")
            # Обновляем кеш с новой ролью
            await cache.set(f"user:username:{updated_user.username}", updated_user)

        # Формируем текст подтверждения
        admin_username = callback.from_user.username or f"ID:{admin_tg_id}"
        target_username = updated_user.username or f"ID:{updated_user.tg_id}"
        username_display = (
            updated_user.username
            if updated_user.username
            else f"ID:{updated_user.tg_id}"
        )
        role_display = {
            UserRole.ADMIN: "👑 Администратор",
            UserRole.MODERATOR: "🛡️ Модератор",
            UserRole.USER: "👤 Пользователь",
        }.get(new_role, "❓ Неизвестно")

        text = (
            f"✅ <b>Роль успешно изменена</b>\n\n"
            f"👤 Пользователь: @{username_display}\n"
            f"📋 Новая роль: {role_display}\n\n"
            f"Роль изменена с {old_role.value} на {new_role.value}"
        )

        # Обновляем сообщение с новой ролью
        await callback.message.edit_text(
            text=text,
            reply_markup=role_select_ikb(
                user_id=updated_user.id, current_role=new_role
            ),
        )

        logger.info(
            f"Админ {admin_username} ({admin_tg_id}) изменил роль пользователя "
            f"@{target_username} ({updated_user.id}) с {old_role.value} на {new_role.value}"
        )

    except ValueError as e:
        logger.error(f"Ошибка парсинга данных в role_select_callback_handler: {e}")
        await callback.message.edit_text("❌ Ошибка: неверный формат данных")
    except Exception as e:
        logger.error(f"Ошибка при изменении роли: {e}", exc_info=True)
        await callback.message.edit_text("❌ Произошла ошибка при изменении роли")
