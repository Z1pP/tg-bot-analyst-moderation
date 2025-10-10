from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from models.user import User, UserRole


@dataclass
class UserDTO:
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

    def to_dict(self) -> dict:
        """
        Преобразует DTO в словарь

        Returns:
            dict: Словарь с данными пользователя
        """
        return {
            "id": self.id,
            "tg_id": self.tg_id,
            "username": self.username,
            "role": self.role.value,
            "is_active": self.is_active,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UserDTO":
        """
        Создает DTO из словаря

        Args:
            data: Словарь с данными пользователя

        Returns:
            UserDTO: DTO пользователя
        """
        return cls(
            id=data["id"],
            tg_id=data.get("tg_id"),
            username=data.get("username"),
            role=UserRole(data["role"]),
            is_active=data["is_active"],
        )


@dataclass
class CreateUserDTO:
    """DTO для создания нового пользователя"""

    tg_id: str
    username: str
    role: UserRole = UserRole.MODERATOR
    is_active: bool = True


@dataclass
class UpdateUserDTO:
    """DTO для обновления пользователя"""

    id: int
    tg_id: Optional[str] = None
    username: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

    def to_dict(self) -> dict:
        """
        Преобразует DTO в словарь, исключая None значения

        Returns:
            dict: Словарь с данными для обновления
        """
        return {
            k: v
            for k, v in {
                "id": self.id,
                "tg_id": self.tg_id,
                "username": self.username,
                "role": self.role.value if self.role else None,
                "is_active": self.is_active,
            }.items()
            if v is not None
        }


@dataclass
class DbUserDTO:
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
