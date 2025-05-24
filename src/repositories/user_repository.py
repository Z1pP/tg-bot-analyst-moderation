import logging
from datetime import datetime
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

                return result.scalars().all()
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
                    created_at=datetime.now(),
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)
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
            except Exception as e:
                logger.error("An error occurred when deleting a user: %s", str(e))
                await session.rollback()
                raise e
