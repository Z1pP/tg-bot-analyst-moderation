"""DTO для use cases времени (текущее время приложения, конвертация в локальную зону)."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class GetAppNowDTO(BaseModel):
    """Пустой DTO для запроса текущего времени в часовом поясе приложения."""

    model_config = ConfigDict(frozen=True)


class ConvertToLocalTimeDTO(BaseModel):
    """DTO для конвертации datetime в локальную временную зону приложения."""

    dt: Optional[datetime] = None

    model_config = ConfigDict(frozen=True)
