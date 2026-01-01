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

    @classmethod
    def from_model(cls, user: "User") -> "UserDTO":
        """
        Создает DTO из модели User

        Args:
            user: Модель пользователя

        Returns:
            UserDTO: DTO пользователя
        """
        return cls(
            id=user.id,
            tg_id=user.tg_id,
            username=user.username,
            role=user.role,
            is_active=user.is_active,
        )
