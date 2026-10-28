"""DTO для просмотра логов действий администраторов."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class AdminWithLogsDTO(BaseModel):
    """Администратор с логами для списка выбора."""

    id: int
    username_display: str
    tg_id: str

    model_config = ConfigDict(frozen=True)


class GetAdminLogsPageDTO(BaseModel):
    """Входные данные для получения страницы логов. admin_id=None — логи всех админов."""

    admin_id: Optional[int] = None
    page: int = 1
    limit: int = 10

    model_config = ConfigDict(frozen=True)


class AdminLogPageResultDTO(BaseModel):
    """Результат страницы логов: заголовок и готовые строки записей."""

    header_text: str
    entry_lines: list[str]
    total_count: int

    model_config = ConfigDict(frozen=True)


class AdminLogItemDTO(BaseModel):
    """Одна запись лога администратора для API."""

    id: int
    action_type: str
    details: Optional[str] = None
    admin_username: Optional[str] = None
    admin_tg_id: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(frozen=True)


class AdminLogsPageResultDTO(BaseModel):
    """Страница логов администраторов для API."""

    items: list[AdminLogItemDTO]
    total: int
    page: int
    limit: int

    model_config = ConfigDict(frozen=True)
