import logging
from typing import Optional

from sqlalchemy import select

from constants.enums import UserRole
from database.session import async_session
from models import User

logger = logging.getLogger(__name__)


class UserRepository:
    async def get_user_by_tg_id(self, tg_id: str) -> Optional[User]:
        async with async_session() as session:
            try:
                result = await session.execute(select(User).where(User.tg_id == tg_id))
                user = result.scalars().first()

                logger.info("Received user: %s", user)

                return user
            except Exception as e:
                logger.error("An error occurred when receiving a user: %s", str(e))
                return None

    async def get_all_users(self) -> list[User]:
        async with async_session() as session:
            try:
                result = await session.execute(
                    select(User)
                    .where(
                        User.role == UserRole.MODERATOR,
                    )
                    .order_by(User.username),
                )

                users = result.scalars().all()

                logger.info("Received users: %s", len(users))

                return users
            except Exception as e:
                logger.error("An error occurred when receiving a user: %s", str(e))
                return None

    async def get_user_by_username(self, username: str) -> Optional[User]:
        async with async_session() as session:
            try:
                result = await session.execute(
                    select(User).where(User.username == username)
                )
                user = result.scalars().first()

                logger.info("Received user: %s", user)

                return user
            except Exception as e:
                logger.error("An error occurred when receiving a user: %s", str(e))
                return None

    async def create_user(
        self,
        tg_id: str = None,
        username: str = None,
        role: Optional[UserRole] = None,
    ) -> User:
        if tg_id is None and username is None:
            raise ValueError("tg_id or username must be provided")

        async with async_session() as session:
            try:
                user = User(
                    tg_id=tg_id,
                    username=username,
                    role=role,
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)

                logger.info("Created user: %s", user)

                return user
            except Exception as e:
                logger.error("An error occurred when creating a user: %s", str(e))
                await session.rollback()
                raise e

    async def delete_user(self, user: User) -> None:
        async with async_session() as session:
            try:
                await session.delete(user)
                await session.flush()
                await session.commit()

                logger.info("Deleted user with id = %s", user.id)
            except Exception as e:
                logger.error("An error occurred when deleting a user: %s", str(e))
                await session.rollback()
                raise e
