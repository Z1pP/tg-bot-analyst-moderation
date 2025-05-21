from aiogram import F, Router
from aiogram.types import Message

from constants import KbCommands
from container import container
from keyboards.inline.moderators import moderators_inline_kb
from keyboards.reply.menu import get_moderators_list_kb
from usecases.user import GetAllUsersUseCase
from utils.exception_handler import handle_exception
from utils.send_message import send_html_message_with_kb

router = Router(name=__name__)


@router.message(F.text == KbCommands.GET_MODERATORS_LIST)
async def moderators_list_handler(message: Message) -> None:
    """
    Обработчик команды для получения списка модераторов.
    """
    username = message.from_user.username

    try:
        usecase: GetAllUsersUseCase = container.resolve(GetAllUsersUseCase)

        users = await usecase.execute(admin_username=username)

        if not users:
            await send_html_message_with_kb(
                message=message,
                text="Список модераторов пуст. Добавьте модераторов",
                reply_markup=get_moderators_list_kb(),
            )

        await send_html_message_with_kb(
            message=message,
            text=f"Всего {len(users)} модераторов",
            reply_markup=moderators_inline_kb(users),
        )
    except Exception as e:
        await handle_exception(
            message=message,
            exc=e,
            context="moderators_list_handler",
        )
