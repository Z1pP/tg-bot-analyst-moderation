from aiogram import F, Router
from aiogram.types import CallbackQuery

from container import container
from keyboards.inline.chats_kb import chat_info_inline_kb, tracked_chats_inline_kb
from repositories import ChatTrackingRepository
from repositories.user_repository import UserRepository
from utils.exception_handler import handle_exception

router = Router(name=__name__)


@router.callback_query(F.data.startswith("chat_info_back"))
async def chat_info_back_callback(query: CallbackQuery) -> None:
    try:
        username = query.from_user.username

        # Получаем репозиторий
        chat_tracking_repo: ChatTrackingRepository = container.resolve(
            ChatTrackingRepository
        )

        user_repo: UserRepository = container.resolve(UserRepository)

        admin = await user_repo.get_user_by_username(username=username)

        # Получаем список трекающих чатов
        chats = await chat_tracking_repo.get_all_tracked_chats(admin_id=admin.id)

        await query.message.edit_text(
            text="Список трекающих чатов:",
            reply_markup=tracked_chats_inline_kb(chats=chats),
        )
    except Exception as e:
        await handle_exception(query.message, e, "chat_info_back_callback")
        await query.answer("Произошла ошибка")


@router.callback_query(F.data.startswith("chat_info__"))
async def chat_info_callback(query: CallbackQuery) -> None:
    try:
        chat_id = int(query.data.split("__")[1])

        username = query.from_user.username

        # Получаем репозиторий
        chat_tracking_repo: ChatTrackingRepository = container.resolve(
            ChatTrackingRepository
        )

        user_repo: UserRepository = container.resolve(UserRepository)

        admin = await user_repo.get_user_by_username(username=username)

        # Получаем текущий доступ
        access = await chat_tracking_repo.get_access(admin_id=admin.id, chat_id=chat_id)

        text = "Укажите, какую функцию будет выполнять выбранный вами чат:"

        await query.message.edit_text(
            text=text,
            reply_markup=chat_info_inline_kb(access=access),
        )
    except Exception as e:
        await handle_exception(query.message, e, "chat_info_callback")
        await query.answer("Произошла ошибка")


@router.callback_query(F.data.startswith("toggle_target__"))
async def toggle_target_status_callback(query: CallbackQuery) -> None:
    """
    Обработчик для переключения статуса чата как получателя отчетов.
    """
    try:
        # Получаем ID чата из callback_data
        chat_id = int(query.data.split("__")[1])

        username = query.from_user.username

        # Получаем репозиторий
        chat_tracking_repo: ChatTrackingRepository = container.resolve(
            ChatTrackingRepository
        )

        user_repo: UserRepository = container.resolve(UserRepository)

        admin = await user_repo.get_user_by_username(username=username)

        # Получаем текущий доступ
        access = await chat_tracking_repo.get_access(admin_id=admin.id, chat_id=chat_id)

        # Определяем новый статус (инвертируем текущий)
        new_status = not access.is_target if access else True

        # Устанавливаем новый статус
        result = await chat_tracking_repo.set_chat_as_target(
            admin_id=admin.id, chat_id=chat_id, is_target=new_status
        )

        if result:
            # Получаем обновленный список чатов
            chats = await chat_tracking_repo.get_all_tracked_chats(admin_id=admin.id)

            await query.message.edit_reply_markup(
                reply_markup=tracked_chats_inline_kb(chats=chats)
            )

            # Показываем уведомление
            status_text = "включена" if new_status else "отключена"
            await query.answer(f"Рассылка {status_text}")
        else:
            await query.answer("Не удалось изменить статус")

    except Exception as e:
        await handle_exception(query.message, e, "toggle_target_status_callback")
        await query.answer("Произошла ошибка")
