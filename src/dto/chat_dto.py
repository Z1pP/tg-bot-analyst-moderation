from dataclasses import dataclass

from models import ChatSession


@dataclass
class ChatDTO:
    chat_id: str
    title: str


@dataclass
class ChatReadDTO(ChatDTO):
    id: int

    @classmethod
    def from_entity(cls, chat: ChatSession) -> "ChatReadDTO":
        """
        Создает DTO из модели ChatSession

        Args:
            chat: Модель сессии чата

        Returns:
            CharReadDTO: DTO сессии чата
        """
        return cls(
            id=chat.id,
            chat_id=chat.chat_id,
            title=chat.title,
        )
