import argparse
import asyncio
import logging

from constants.enums import UserRole
from container import ContainerSetup, container
from database.session import async_session
from repositories.user_repository import UserRepository
from utils.data_parser import parse_and_validate_tg_id

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Инициализация контейнера
ContainerSetup.setup()


async def manage_user_role(tg_id: str, role: str, username: str | None) -> None:
    """
    Creates a new user or updates an existing user's role and username.

    Args:
        tg_id (str): Telegram ID of the user.
        role (str): The desired role for the user.
        username (str | None): The Telegram username of the user.

    Raises:
        ValueError: If tg_id is invalid.
        Exception: For database access errors.
    """
    valid_tg_id = parse_and_validate_tg_id(tg_id=tg_id)
    if not valid_tg_id:
        raise ValueError(f"Invalid TG_ID format: {tg_id}")

    user_repo: UserRepository = container.resolve(UserRepository)
    new_role = UserRole(role)

    try:
        async with async_session() as session:
            async with session.begin():
                user = await user_repo.get_user_by_tg_id(tg_id=valid_tg_id)

                if user:
                    # Update existing user
                    if user.role != new_role or (
                        username and user.username != username
                    ):
                        old_role = user.role.value
                        user.role = new_role
                        if username:
                            user.username = username

                        session.add(user)
                        await session.flush()
                        await session.refresh(user)

                        logger.info(
                            f"User TG_ID:{tg_id} updated. Role changed from {old_role} to {user.role.value}."
                        )
                        print(f"User TG_ID:{tg_id} role updated to {user.role.value}.")
                    else:
                        logger.info(
                            f"User TG_ID:{tg_id} already has the role '{user.role.value}' and specified username."
                        )
                        print(
                            f"User TG_ID:{tg_id} already has the role '{user.role.value}'."
                        )
                else:
                    # Create new user
                    user = await user_repo.create_user(tg_id=valid_tg_id, role=new_role)
                    if username:
                        user.username = username

                    session.add(user)
                    await session.flush()
                    await session.refresh(user)

                    logger.info(
                        f"User TG_ID:{tg_id} created with role '{user.role.value}'."
                    )
                    print(f"User TG_ID:{tg_id} created with role '{user.role.value}'.")

    except Exception as e:
        logger.error(f"Error managing user: {e}", exc_info=True)
        print(f"An error occurred: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Create a new user or update an existing user's role."
    )
    parser.add_argument("--tg_id", type=str, required=True, help="Telegram user_id")
    parser.add_argument("--username", type=str, help="Telegram username (optional)")
    parser.add_argument(
        "--role",
        type=str,
        default=UserRole.USER.value,
        choices=[role.value for role in UserRole],
        help=f"User role (default: {UserRole.USER.value})",
    )

    args = parser.parse_args()
    asyncio.run(
        manage_user_role(tg_id=args.tg_id, role=args.role, username=args.username)
    )


if __name__ == "__main__":
    main()
