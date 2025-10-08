from typing import Any, Awaitable, Callable, Dict, Optional

from aiogram import BaseMiddleware
from aiogram.types import Message

from dto.user_dto import UserDTO
from services import ChatService, UserService


class UserDTOMiddleware(BaseMiddleware):
    def __init__(self, user_service: UserService, chat_service: Optional[ChatService] = None):
        self.user_service = user_service
        self.chat_service = chat_service

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        user = await self.user_service.get_user(
            tg_id=event.from_user.id,
            username=event.from_user.username,
        )

        data["user_dto"] = UserDTO(
            id=user.id,
            tg_id=user.tg_id,
            username=user.username,
            role=user.role,
            is_tracked=user.is_tracked,
        )

        if self.chat_service and event.chat.type in ["group", "supergroup"]:
            chat = await self.chat_service.get_chat(
                chat_id=event.chat.id,
                title=event.chat.title,
            )
            if chat:
                from dto.chat_dto import ChatDTO
                data["chat_dto"] = ChatDTO(
                    id=chat.id,
                    chat_id=chat.chat_id,
                    title=chat.title,
                )

        return await handler(event, data)
