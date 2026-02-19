import logging

from aiogram import Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import Message
from punq import Container

from constants import Dialog
from dto.chat_dto import GetChatWithArchiveDTO
from usecases.chat import GetChatWithArchiveUseCase
from usecases.moderation import VerifyMemberUseCase

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.message(CommandStart(deep_link=True))
async def antibot_start_handler(
    message: Message, command: CommandObject, container: Container
) -> None:
    """
    Обработчик антибот-верификации через deep link.
    Доступен всем пользователям (не только админам).
    """
    if command.args and command.args.startswith("v_"):
        verify_usecase: VerifyMemberUseCase = container.resolve(VerifyMemberUseCase)
        success, chat_tgid = await verify_usecase.execute(
            payload=command.args, clicking_user_id=message.from_user.id
        )

        if success:
            get_chat_uc: GetChatWithArchiveUseCase = container.resolve(
                GetChatWithArchiveUseCase
            )
            chat_db = await get_chat_uc.execute(
                GetChatWithArchiveDTO(chat_tgid=chat_tgid)
            )
            chat_title = chat_db.title if chat_db else "чате"
            await message.answer(
                Dialog.Antibot.VERIFIED_SUCCESS.format(chat_title=chat_title),
                parse_mode="HTML",
            )
            return
        elif chat_tgid:  # Если была попытка, но неуспешно (не тот юзер)
            await message.answer(Dialog.Antibot.VERIFIED_ERROR_USER)
            return
