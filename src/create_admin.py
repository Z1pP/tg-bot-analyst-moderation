"""
Скрипт для создания администраторов в системе.

Этот скрипт позволяет добавлять новых администраторов в базу данных
или проверять существование уже созданных администраторов.

Использование:
    python create_admin.py --username <username> [--role <role>]

Аргументы:
    --username: Имя пользователя администратора (обязательный)
    --role: Роль пользователя (по умолчанию "creator")
"""

import argparse
import asyncio
import logging

from constants.enums import UserRole
from container import container
from usecases.user import GetOrCreateUserIfNotExistUserCase
from utils.username_validator import parse_and_validate_username

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def get_or_create_admin(username: str, role: str) -> None:
    """
    Создает нового администратора или проверяет его существование.

    Args:
        username (str): Имя пользователя для создания/проверки
        role (str): Роль пользователя в системе

    Returns:
        None

    Raises:
        ValueError: Если имя пользователя недействительно
        Exception: При ошибках доступа к базе данных или других проблемах
    """
    # Валидируем username
    valid_username = parse_and_validate_username(username)
    if not valid_username:
        logger.error(f"Invalid username: {username}")
        raise ValueError(f"Invalid username format: {username}")

    # Получаем usecase из контейнера
    usecase: GetOrCreateUserIfNotExistUserCase = container.resolve(
        GetOrCreateUserIfNotExistUserCase
    )

    try:
        # Создаем или получаем пользователя
        result = await usecase.execute(
            username=valid_username,
            role=UserRole(role),
        )

        if result.is_existed:
            logger.info(
                f"User {username} already exists with role {result.user.role.value}"
            )
            print(f"User {username} already exists")
            return

        logger.info(f"User {username} created with role {role}")
        print(f"User {username} created")
    except Exception as e:
        logger.error(f"Error creating/checking admin user: {e}", exc_info=True)
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create or check admin users in the system"
    )
    parser.add_argument("--username", type=str, required=True, help="Admin username")
    parser.add_argument(
        "--role",
        type=str,
        required=False,
        default="admin",
        choices=["admin", "moderator", "user"],
        help="User role (default: admin)",
    )
    args = parser.parse_args()

    asyncio.run(get_or_create_admin(username=args.username, role=args.role))
