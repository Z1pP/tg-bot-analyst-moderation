import logging

from aiogram import F, Router
from aiogram.types import Message

from constants import KbCommands
from constants.pagination import USERS_PAGE_SIZE
from container import container
from keyboards.inline.users import users_inline_kb
from keyboards.reply.menu import user_menu_kb
from states import MenuStates
from usecases.user_tracking import GetListTrackedUsersUseCase
from utils.exception_handler import handle_exception
from utils.send_message import send_html_message_with_kb

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.message(F.text == KbCommands.GET_STATISTICS, MenuStates.users_menu)
@router.message(F.text == KbCommands.SELECT_USER)
async def users_list_handler(message: Message) -> None:
    """Обработчик команды для отображения списка пользователей.
    Через inline клавиатуру
    """
    try:
        logger.info(
            f"Пользователь {message.from_user.id} запросил список пользователей для отчета"
        )

        usecase: GetListTrackedUsersUseCase = container.resolve(
            GetListTrackedUsersUseCase
        )
        users = await usecase.execute(admin_tgid=str(message.from_user.id))

        if not users:
            message_text = (
                "❗Чтобы получать отчёты по пользователям, "
                "необходимо добавить пользователя в отслеживаемые"
            )
            await send_html_message_with_kb(
                message=message,
                text=message_text,
                reply_markup=user_menu_kb(),
            )
            return

        logger.info(f"Найдено {len(users)} пользователей для отчета")

        # Показываем первую страницу
        first_page_users = users[:USERS_PAGE_SIZE]

        await send_html_message_with_kb(
            message=message,
            text=f"Всего {len(users)} пользователей",
            reply_markup=users_inline_kb(
                users=first_page_users,
                page=1,
                total_count=len(users),
            ),
        )
    except Exception as e:
        await handle_exception(message, e, "users_list_handler")
