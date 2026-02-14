import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy import and_, delete, func, select

from constants.enums import UserRole
from models import (
    AdminChatAccess,
    ChatMessage,
    ChatSession,
    MessageReaction,
    User,
    admin_user_tracking,
)
from repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository):
    async def total_active_users(
        self,
        chat_id: int,
        start_date: datetime,
        end_date: datetime,
    ) -> int:
        """Получает общее количество активных пользователей в чате."""

        async with self._db.session() as session:
            try:
                msg_users = select(ChatMessage.user_id).where(
                    and_(
                        ChatMessage.chat_id == chat_id,
                        ChatMessage.created_at.between(start_date, end_date),
                    )
                )

                react_users = select(MessageReaction.user_id).where(
                    and_(
                        MessageReaction.created_at.between(start_date, end_date),
                        MessageReaction.chat_id == chat_id,
                    )
                )

                active_users_union = msg_users.union(react_users).subquery()

                stmt = select(func.count()).select_from(active_users_union)

                count = await session.scalar(stmt)

                logger.info("Общее количество активных пользователей: %s", count)
                return count
            except Exception as e:
                logger.error(
                    "Ошибка при получении общего количества активных пользователей: %s",
                    e,
                )

    async def update_user(
        self, user_id: int, username: str, check_changes: bool = False
    ) -> Optional[User]:
        """Обновляет username пользователя."""
        async with self._db.session() as session:
            try:
                user = await session.get(User, user_id)
                if not user:
                    logger.warning("Пользователь %s не найден", user_id)
                    return None

                if check_changes and user.username == username:
                    return user

                user.username = username
                await session.commit()
                await session.refresh(user)
                logger.info(
                    "Username обновлен для пользователя %s: %s",
                    user_id,
                    username,
                )
                return user
            except Exception as e:
                logger.error(
                    "Ошибка при обновлении username пользователя %s: %s",
                    user_id,
                    e,
                )
                await session.rollback()
                raise

    async def get_user_by_tg_id(self, tg_id: str) -> Optional[User]:
        """Получает пользователя по Telegram ID."""
        async with self._db.session() as session:
            try:
                result = await session.execute(
                    select(User).where(User.tg_id == tg_id),
                )
                user = result.scalars().first()

                if user:
                    logger.info(
                        "Получен пользователь по tg_id=%s: username=%s, role=%s",
                        tg_id,
                        user.username,
                        user.role,
                    )
                else:
                    logger.info("Пользователь с tg_id=%s не найден", tg_id)

                return user
            except Exception as e:
                logger.error(
                    "Ошибка при получении пользователя по tg_id=%s: %s", tg_id, e
                )
                return None

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Получает пользователя по ID."""
        async with self._db.session() as session:
            try:
                result = await session.execute(select(User).where(User.id == user_id))
                user = result.scalars().first()

                if user:
                    logger.info(
                        "Получен пользователь по id=%d: username=%s, role=%s",
                        user_id,
                        user.username,
                        user.role,
                    )
                else:
                    logger.info("Пользователь с id=%d не найден", user_id)

                return user
            except Exception as e:
                logger.error(
                    "Ошибка при получении пользователя по id=%d: %s", user_id, e
                )
                return None

    async def get_tracked_users_for_admin(self, admin_tg_id: str) -> List[User]:
        async with self._db.session() as session:
            try:
                # Получаем админа
                admin_query = select(User).where(User.tg_id == admin_tg_id)
                admin_result = await session.execute(admin_query)
                admin = admin_result.scalars().first()

                if not admin:
                    logger.warning("Администратор с TG_ID:%s не найден", admin_tg_id)
                    return []

                # Получаем отслеживаемых пользователей
                query = (
                    select(User)
                    .join(
                        admin_user_tracking,
                        User.id == admin_user_tracking.c.tracked_user_id,
                    )
                    .where(admin_user_tracking.c.admin_id == admin.id)
                    .order_by(func.coalesce(User.username, User.tg_id))
                )
                result = await session.execute(query)

                tracked_users = result.scalars().all()
                logger.info(
                    "Получено %d отслеживаемых пользователей для администратора TG_ID:%s",
                    len(tracked_users),
                    admin_tg_id,
                )
                return tracked_users
            except Exception as e:
                logger.error(
                    "Ошибка при получении отслеживаемых пользователей для администратора с TG_ID:%s: %s",
                    admin_tg_id,
                    e,
                )
                raise

    async def get_admins_for_chat(self, chat_tg_id: str) -> Optional[List[User]]:
        async with self._db.session() as session:
            try:
                query = (
                    select(User)
                    .join(AdminChatAccess, User.id == AdminChatAccess.admin_id)
                    .join(ChatSession, AdminChatAccess.chat_id == ChatSession.id)
                    .where(ChatSession.chat_id == chat_tg_id)
                )
                result = await session.execute(query)
                admins = result.scalars().all()

                logger.info(
                    "Получено %d администраторов для чата TG_ID:%s",
                    len(admins),
                    chat_tg_id,
                )
                return admins
            except Exception as e:
                logger.error(
                    "Ошибка при получении администраторов для чата TG_ID:%s: %s",
                    chat_tg_id,
                    e,
                )
                raise

    async def get_all_moderators(self) -> List[User]:
        """Получает список всех модераторов."""
        async with self._db.session() as session:
            try:
                result = await session.execute(
                    select(User)
                    .where(
                        User.role == UserRole.MODERATOR,
                    )
                    .order_by(User.username),
                )

                users = result.scalars().all()
                logger.info("Получено %d модераторов", len(users))
                return users
            except Exception as e:
                logger.error("Ошибка при получении списка модераторов: %s", e)
                return []

    async def get_owners_and_admins(self, language: str | None = None) -> List[User]:
        """
        Получает пользователей с ролями OWNER и ADMIN.
        Если указан language (ru/en), возвращает только с совпадающим языком интерфейса.
        """
        async with self._db.session() as session:
            try:
                stmt = (
                    select(User)
                    .where(
                        User.role.in_((UserRole.OWNER, UserRole.ADMIN)),
                        User.is_active.is_(True),
                    )
                    .order_by(User.username)
                )
                result = await session.execute(stmt)
                users = list(result.scalars().all())
                if language:
                    lang_normalized = language.split("-")[0].lower()
                    users = [
                        u
                        for u in users
                        if u.language
                        and u.language.split("-")[0].lower() == lang_normalized
                    ]
                logger.info(
                    "Получено %d владельцев/админов (language=%s)",
                    len(users),
                    language,
                )
                return users
            except Exception as e:
                logger.error("Ошибка при получении владельцев/админов: %s", e)
                return []

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Получает пользователя по имени пользователя (регистронезависимо)."""
        async with self._db.session() as session:
            try:
                result = await session.execute(
                    select(User).where(
                        func.lower(User.username) == func.lower(username)
                    )
                )
                user = result.scalars().first()

                if user:
                    logger.info(
                        "Получен пользователь по username=%s: id=%s, role=%s",
                        username,
                        user.id,
                        user.role,
                    )
                else:
                    logger.info("Пользователь с username=%s не найден", username)

                return user
            except Exception as e:
                logger.error(
                    "Ошибка при получении пользователя по username=%s: %s", username, e
                )
                return None

    async def create_user(
        self,
        tg_id: str = None,
        username: str = None,
        role: Optional[UserRole] = UserRole.USER,
        language: str = "ru",
    ) -> User:
        """Создает нового пользователя."""
        if tg_id is None and username is None:
            raise ValueError("tg_id или username должны быть указаны")

        async with self._db.session() as session:
            try:
                user = User(
                    tg_id=tg_id,
                    username=username,
                    role=role,
                    language=language,
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)

                logger.info(
                    "Создан новый пользователь: id=%s, username=%s, role=%s",
                    user.id,
                    user.username,
                    user.role,
                )
                return user
            except Exception as e:
                logger.error(
                    "Ошибка при создании пользователя (username=%s): %s", username, e
                )
                await session.rollback()
                raise e

    async def update_user_language(self, user_id: int, language: str) -> Optional[User]:
        """Обновляет язык пользователя."""
        async with self._db.session() as session:
            try:
                user = await session.get(User, user_id)
                if not user:
                    logger.warning("Пользователь %s не найден", user_id)
                    return None

                user.language = language
                await session.commit()
                await session.refresh(user)
                logger.info(
                    "Язык обновлен для пользователя %s: %s",
                    user_id,
                    language,
                )
                return user
            except Exception as e:
                logger.error(
                    "Ошибка при обновлении языка пользователя %s: %s",
                    user_id,
                    e,
                )
                await session.rollback()
                raise

    async def update_user_role(
        self, user_id: int, new_role: UserRole
    ) -> Optional[User]:
        """Обновляет роль пользователя."""
        async with self._db.session() as session:
            try:
                user = await session.get(User, user_id)
                if not user:
                    logger.warning("Пользователь %s не найден", user_id)
                    return None

                old_role = user.role
                user.role = new_role
                await session.commit()
                await session.refresh(user)
                logger.info(
                    "Роль обновлена для пользователя %s: %s -> %s",
                    user_id,
                    old_role.value,
                    new_role.value,
                )
                return user
            except Exception as e:
                logger.error(
                    "Ошибка при обновлении роли пользователя %s: %s",
                    user_id,
                    e,
                )
                await session.rollback()
                raise

    async def delete_user(self, user_id: int) -> bool:
        """Удаляет пользователя по его ID"""
        async with self._db.session() as session:
            try:
                query = delete(User).where(User.id == user_id)
                result = await session.execute(query)
                await session.commit()

                deleted_count = result.rowcount
                if deleted_count > 0:
                    logger.info("Удален пользователь с ID=%s", user_id)
                    return True
                else:
                    logger.warning(
                        "Пользователь с ID=%s не найден для удаления",
                        user_id,
                    )
                    return False
            except Exception as e:
                logger.error("Ошибка при удалении пользователя с ID=%s:%s", user_id, e)
                await session.rollback()
                raise e
