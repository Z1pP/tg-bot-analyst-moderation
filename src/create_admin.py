import argparse
import asyncio
import logging

from constants.enums import UserRole
from container import container
from usecases.user import GetOrCreateUserIfNotExistUserCase
from utils.username_validator import parse_and_validate_tg_id

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def get_or_create_admin(tg_id: str, role: str) -> None:
    """
    Создает нового администратора или проверяет его существование.

    Args:
        tg_id (str): Telegram ID пользователя для создания/проверки
        role (str): Роль пользователя в системе

    Raises:
        ValueError: Если tg_id недействителен
        Exception: При ошибках доступа к базе данных
    """
    valid_tg_id = parse_and_validate_tg_id(tg_id=tg_id)
    if not valid_tg_id:
        raise ValueError(f"Invalid TG_ID format: {tg_id}")

    usecase: GetOrCreateUserIfNotExistUserCase = container.resolve(
        GetOrCreateUserIfNotExistUserCase
    )

    try:
        result = await usecase.execute(
            tg_id=valid_tg_id,
            role=UserRole(role),
        )

        if result.is_existed:
            logger.info(
                f"User with TG_ID:{tg_id} already exists with role {result.user.role.value}"
            )
            print(f"User with TG_ID:{tg_id} already exists")
        else:
            logger.info(f"User TG_ID:{tg_id} created with role {role}")
            print(f"User TG_ID:{tg_id} created")

    except Exception as e:
        logger.error(f"Error creating/checking admin user: {e}", exc_info=True)
        print(f"An error occurred: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Create or check admin users in the system"
    )
    parser.add_argument(
        "--tg_id", type=str, required=True, help="Admin telegram user_id"
    )
    parser.add_argument(
        "--role",
        type=str,
        default="admin",
        choices=["admin", "moderator", "user"],
        help="User role (default: admin)",
    )

    args = parser.parse_args()
    asyncio.run(get_or_create_admin(tg_id=args.tg_id, role=args.role))


if __name__ == "__main__":
    main()
