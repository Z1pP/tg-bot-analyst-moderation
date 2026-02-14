"""DTO для операций с релизными заметками."""

from pydantic import BaseModel, ConfigDict


class ReleaseNoteItemDTO(BaseModel):
    """Элемент списка заметок для меню (id и заголовок)."""

    id: int
    title: str

    model_config = ConfigDict(frozen=True)


class GetReleaseNotesPageDTO(BaseModel):
    """Входные данные для получения страницы заметок."""

    language: str
    page: int = 1
    page_size: int = 10

    model_config = ConfigDict(frozen=True)


class ReleaseNotesPageResultDTO(BaseModel):
    """Результат страницы заметок."""

    notes: list[ReleaseNoteItemDTO]
    total_pages: int
    page: int

    model_config = ConfigDict(frozen=True)


class GetReleaseNoteByIdDTO(BaseModel):
    """Входные данные для получения заметки по ID."""

    note_id: int

    model_config = ConfigDict(frozen=True)


class ReleaseNoteDetailResultDTO(BaseModel):
    """Данные заметки для отображения (заголовок, контент, автор, дата)."""

    note_id: int
    title: str
    content: str
    author_display_name: str
    date_str: str

    model_config = ConfigDict(frozen=True)


class CreateReleaseNoteDTO(BaseModel):
    """Входные данные для создания заметки."""

    title: str
    content: str
    language: str
    author_tg_id: str

    model_config = ConfigDict(frozen=True)


class UpdateReleaseNoteTitleDTO(BaseModel):
    """Входные данные для обновления заголовка заметки."""

    note_id: int
    new_title: str

    model_config = ConfigDict(frozen=True)


class UpdateReleaseNoteContentDTO(BaseModel):
    """Входные данные для обновления содержимого заметки."""

    note_id: int
    new_content: str

    model_config = ConfigDict(frozen=True)


class DeleteReleaseNoteDTO(BaseModel):
    """Входные данные для удаления заметки."""

    note_id: int

    model_config = ConfigDict(frozen=True)


class BroadcastReleaseNoteDTO(BaseModel):
    """Входные данные для рассылки заметки."""

    note_id: int
    sender_tg_id: str

    model_config = ConfigDict(frozen=True)


class BroadcastRecipientDTO(BaseModel):
    """Получатель рассылки: chat_id и текст сообщения."""

    chat_id: int
    text: str

    model_config = ConfigDict(frozen=True)


class BroadcastResultDTO(BaseModel):
    """Результат рассылки: список получателей (chat_id, text) и DTO для экрана просмотра."""

    recipients: list[BroadcastRecipientDTO]
    detail_dto: ReleaseNoteDetailResultDTO

    model_config = ConfigDict(frozen=True)
