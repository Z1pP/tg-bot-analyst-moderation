from dataclasses import dataclass


@dataclass
class ChatDTO:
    chat_id: str
    title: str


@dataclass
class ChatDTOResult(ChatDTO):
    id: int
