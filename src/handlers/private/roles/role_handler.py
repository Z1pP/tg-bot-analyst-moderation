import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from punq import Container

from constants import PROTECTED_USER_TG_ID, Dialog
from constants.callback import CallbackData
from constants.enums import UserRole
from keyboards.inline.roles import cancel_role_select_ikb, role_select_ikb
from repositories import UserRepository
from services.user import UserService
from states import RoleState
from usecases.user import UpdateUserRoleUseCase
from utils.send_message import safe_edit_message
from utils.user_data_parser import parse_data_from_text

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data == CallbackData.Role.INPUT_USER_DATA)
async def input_user_data_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик ввода данных пользователя для изменения роли.
    """
    await callback.answer()
    await state.clear()

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Roles.INPUT_USER_DATA,
        reply_markup=cancel_role_select_ikb(),
    )

    await state.update_data(active_message_id=callback.message.message_id)

    await state.set_state(RoleState.waiting_user_input)


@router.message(RoleState.waiting_user_input)
async def process_user_data_input(
    message: Message, state: FSMContext, container: Container
) -> None:
    """
    Обработчик ввода данных пользователя для изменения роли.
    """

    user_data = parse_data_from_text(text=message.text)
    active_message_id = await state.get_value("active_message_id")

    if not user_data:
        if active_message_id:
            await safe_edit_message(
                bot=message.bot,
                chat_id=message.chat.id,
                message_id=active_message_id,
                text=Dialog.User.INVALID_USERNAME_FORMAT_ADD,
                reply_markup=cancel_role_select_ikb(),
            )
        return

    user_service: UserService = container.resolve(UserService)
    user = None

    if user_data.tg_id:
        user = await user_service.get_user(tg_id=user_data.tg_id)
    elif user_data.username:
        user = await user_service.get_by_username(username=user_data.username)

    if not user:
        if active_message_id:
            await safe_edit_message(
                bot=message.bot,
                chat_id=message.chat.id,
                message_id=active_message_id,
                text=f"❌ Пользователь не найден.\n"
                f"Проверьте правильность введенных данных: {message.text}",
                reply_markup=cancel_role_select_ikb(),
            )
        return

    # Защита от изменения роли для захардкоженного пользователя
    if user.tg_id == PROTECTED_USER_TG_ID:
        if active_message_id:
            await safe_edit_message(
                bot=message.bot,
                chat_id=message.chat.id,
                message_id=active_message_id,
                text="❌ Нельзя изменить роль этому пользователю",
                reply_markup=cancel_role_select_ikb(),
            )
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

    if active_message_id:
        await safe_edit_message(
            bot=message.bot,
            chat_id=message.chat.id,
            message_id=active_message_id,
            text=text,
            reply_markup=role_select_ikb(user_id=user.id, current_role=user.role),
        )

    try:
        await message.delete()
    except Exception:
        pass

    await state.clear()


@router.callback_query(F.data.startswith(CallbackData.User.PREFIX_ROLE_SELECT))
async def role_select_callback_handler(
    callback: CallbackQuery, container: Container
) -> None:
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
            await safe_edit_message(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text="❌ Ошибка: неверный формат данных",
            )
            return

        user_id_str, role_str = parts
        user_id = int(user_id_str)

        # Валидируем роль
        try:
            new_role = UserRole(role_str)
        except ValueError:
            logger.error(f"Неверная роль: {role_str}")
            await safe_edit_message(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=f"❌ Ошибка: неверная роль '{role_str}'",
            )
            return

        # Получаем пользователя
        user_repo: UserRepository = container.resolve(UserRepository)
        user = await user_repo.get_user_by_id(user_id=user_id)

        if not user:
            await safe_edit_message(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text="❌ Пользователь не найден",
            )
            return

        # Защита от изменения роли для захардкоженного пользователя
        if user.tg_id == PROTECTED_USER_TG_ID:
            await safe_edit_message(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text="❌ Нельзя изменить роль этому пользователю",
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

            await safe_edit_message(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=text,
                reply_markup=role_select_ikb(),
            )
            return

        # Обновляем роль
        usecase: UpdateUserRoleUseCase = container.resolve(UpdateUserRoleUseCase)
        updated_user = await usecase.execute(
            user_id=user_id, new_role=new_role, admin_tg_id=admin_tg_id
        )

        if not updated_user:
            await safe_edit_message(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text="❌ Не удалось обновить роль пользователя",
            )
            return

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
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
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
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text="❌ Ошибка: неверный формат данных",
        )
    except Exception as e:
        logger.error(f"Ошибка при изменении роли: {e}", exc_info=True)
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text="❌ Произошла ошибка при изменении роли",
        )
