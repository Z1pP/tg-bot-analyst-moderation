"""DTO для рассылки релизной заметки (текст владельцам и админам по языку)."""

from pydantic import BaseModel, ConfigDict


class BroadcastTextDTO(BaseModel):
    """Входные данные для рассылки текста (без заметки в БД)."""

    text: str
    language: str

    model_config = ConfigDict(frozen=True)


class BroadcastRecipientDTO(BaseModel):
    """Получатель рассылки: chat_id и текст сообщения."""

    chat_id: int
    text: str

    model_config = ConfigDict(frozen=True)
