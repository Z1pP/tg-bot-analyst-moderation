from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from models.user import User, UserRole


class UserDTO(BaseModel):
    """Data Transfer Object для пользователя"""

    # Обязательные поля
    id: int
    role: UserRole
    is_active: bool

    # Опциональные поля
    tg_id: Optional[str] = None
    username: Optional[str] = None
    added_at: Optional[datetime] = None

    @classmethod
    def from_model(cls, user: "User", added_at: Optional[datetime] = None) -> "UserDTO":
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
        )
