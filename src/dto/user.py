from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from constants.enums import UserRole
from models.user import User


class UserDTO(BaseModel):
    """Data Transfer Object для пользователя"""

    id: int
    role: UserRole
    is_active: bool
    tg_id: Optional[str] = None
    username: Optional[str] = None
    added_at: Optional[datetime] = None
    language: Optional[str] = None

    model_config = ConfigDict(frozen=True)

    @classmethod
    def from_model(cls, user: User, added_at: Optional[datetime] = None) -> "UserDTO":
        """
        Создает DTO из модели User

        Args:
            user: Модель пользователя
            added_at: Дата добавления (опционально)

        Returns:
            UserDTO: DTO пользователя
        """
        return cls(
            id=user.id,
            tg_id=user.tg_id,
            username=user.username,
            role=user.role,
            is_active=user.is_active,
            added_at=added_at,
            language=user.language,
        )
