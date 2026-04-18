"""DTO автомодерации (буфер Redis, вызов LLM)."""

from pydantic import BaseModel, ConfigDict, Field


class AutoModerationBufferItemDTO(BaseModel):
    """Одно текстовое сообщение в буфере автомодерации."""

    username: str | None
    user_tg_id: int
    message_id: int
    message_text: str = Field(max_length=4096)

    model_config = ConfigDict(frozen=True)


class SpamDetectionLLMResultDTO(BaseModel):
    """Ответ модели при обнаружении потенциального спамера/бота."""

    user_tg_id: int
    message_id: int
    reason: str = Field(max_length=1024)
    username: str | None = Field(default=None, max_length=255)

    model_config = ConfigDict(frozen=True)


class AutoModerationRunDTO(BaseModel):
    """Входные данные для прогона автомодерации после текстового сообщения в группе."""

    chat_tgid: str
    chat_title: str
    is_auto_moderation_enabled: bool
    archive_chat_tgid: str | None
    username: str | None
    user_tg_id: int
    message_id: int
    message_text: str

    model_config = ConfigDict(frozen=True)


class AutoModerationBatchJobDTO(BaseModel):
    """Пачка сообщений для фоновой обработки (LLM + уведомление в архив)."""

    chat_tgid: str
    chat_title: str
    archive_chat_tgid: str | None
    batch: list[AutoModerationBufferItemDTO]

    model_config = ConfigDict(frozen=True)
