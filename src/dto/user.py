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


class CreateUserDTO(BaseModel):
    """DTO для создания нового пользователя"""

    tg_id: str
    username: str
    role: UserRole = UserRole.MODERATOR
    is_active: bool = True


class UpdateUserDTO(BaseModel):
    """DTO для обновления пользователя"""

    id: int
    tg_id: Optional[str] = None
    username: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class DbUserDTO(BaseModel):
    """DTO для юзера из базы данных"""

    id: int
    tg_id: str
    username: str
    role: UserRole
    is_active: bool
    created_at: datetime

    @classmethod
    def from_model(cls, user: User) -> "DbUserDTO":
        """
        Создает DTO из модели User"""
        return cls(
            id=user.id,
            tg_id=user.tg_id,
            username=user.username,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
        )
