"""DTO для просмотра логов действий администраторов."""

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
