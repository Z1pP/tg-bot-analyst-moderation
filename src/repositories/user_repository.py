import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Select, and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from constants.enums import UserRole
from models import (
    AdminChatAccess,
    ChatMessage,
    ChatSession,
    MessageReaction,
    User,
    admin_user_tracking,
)
from repositories.base import BaseRepository, transactional

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository):
    async def _fetch_user_one(
        self,
        session: AsyncSession,
        where_clause: ColumnElement[bool],
    ) -> Optional[User]:
        """Выполняет запрос одного пользователя по условию. Без логирования и без обработки исключений."""
        result = await session.execute(select(User).where(where_clause))
        first: Optional[User] = result.scalars().first()
        return first

    async def _get_message_user_ids(
        self,
        session: AsyncSession,
        chat_id: int,
        start_date: datetime,
        end_date: datetime,
    ) -> Select[tuple[int]]:
        """Возвращает подзапрос для получения ID пользователей, отправивших сообщения."""
        return select(ChatMessage.user_id).where(
            and_(
                ChatMessage.chat_id == chat_id,
                ChatMessage.created_at.between(start_date, end_date),
            )
        )

    async def _get_reaction_user_ids(
        self,
        session: AsyncSession,
        chat_id: int,
        start_date: datetime,
        end_date: datetime,
    ) -> Select[tuple[int]]:
        """Возвращает подзапрос для получения ID пользователей, поставивших реакции."""
        return select(MessageReaction.user_id).where(
            and_(
                MessageReaction.created_at.between(start_date, end_date),
                MessageReaction.chat_id == chat_id,
            )
        )

    @transactional
    async def total_active_users(
        self,
        session: AsyncSession,
        /,
        chat_id: int,
        start_date: datetime,
        end_date: datetime,
    ) -> int:
        """Получает общее количество активных пользователей в чате."""
        msg_users = await self._get_message_user_ids(
            session, chat_id, start_date, end_date
        )
        react_users = await self._get_reaction_user_ids(
            session, chat_id, start_date, end_date
        )

        active_users_union = msg_users.union(react_users).subquery()
        stmt = select(func.count()).select_from(active_users_union)

        count = await session.scalar(stmt)
        out = int(count) if count is not None else 0
        logger.info("Общее количество активных пользователей: %s", out)
        return out

    @transactional
    async def update_user(
        self,
        session: AsyncSession,
        /,
        user_id: int,
        username: Optional[str],
        check_changes: bool = False,
    ) -> Optional[User]:
        """Обновляет username пользователя (None — очищает устаревший username)."""
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

    @transactional
    async def get_user_by_tg_id(
        self, session: AsyncSession, /, tg_id: str
    ) -> Optional[User]:
        """Получает пользователя по Telegram ID."""
        user = await self._get_one_by_field(session, User, "tg_id", tg_id)
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

    @transactional
    async def get_user_by_id(
        self, session: AsyncSession, user_id: int
    ) -> Optional[User]:
        """Получает пользователя по ID."""
        user = await self._get_one_by_field(session, User, "id", user_id)
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

    @transactional
    async def get_tracked_users_for_admin(
        self, session: AsyncSession, admin_tg_id: str
    ) -> List[User]:
        """Получает список отслеживаемых пользователей для администратора."""
        # Получаем админа
        admin = await self._get_one_by_field(session, User, "tg_id", admin_tg_id)

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

        tracked_users = list(result.scalars().all())
        logger.info(
            "Получено %d отслеживаемых пользователей для администратора TG_ID:%s",
            len(tracked_users),
            admin_tg_id,
        )
        return tracked_users

    @transactional
    async def get_admins_for_chat(
        self, session: AsyncSession, chat_tg_id: str
    ) -> Optional[List[User]]:
        """Получает список администраторов для чата."""
        query = (
            select(User)
            .join(AdminChatAccess, User.id == AdminChatAccess.admin_id)
            .join(ChatSession, AdminChatAccess.chat_id == ChatSession.id)
            .where(ChatSession.chat_id == chat_tg_id)
        )
        result = await session.execute(query)
        admins = list(result.scalars().all())

        logger.info(
            "Получено %d администраторов для чата TG_ID:%s",
            len(admins),
            chat_tg_id,
        )
        return admins

    @transactional
    async def get_users_with_role(
        self, session: AsyncSession, role: UserRole
    ) -> List[User]:
        """Получает пользователей с указанной ролью и непустым tg_id (для рассылки в личку)."""
        result = await session.execute(
            select(User)
            .where(
                User.role == role,
                User.tg_id.isnot(None),
                User.tg_id != "",
            )
            .order_by(User.username),
        )
        users = list(result.scalars().all())
        logger.debug("Получено пользователей с ролью %s: %d", role.value, len(users))
        return users

    @transactional
    async def get_all_moderators(self, session: AsyncSession, /) -> List[User]:
        """Получает список всех модераторов."""
        result = await session.execute(
            select(User)
            .where(
                User.role == UserRole.MODERATOR,
            )
            .order_by(User.username),
        )

        users = list(result.scalars().all())
        logger.info("Получено %d модераторов", len(users))
        return users

    @transactional
    async def get_owners_and_admins(
        self, session: AsyncSession, language: str | None = None
    ) -> List[User]:
        """
        Получает пользователей с ролями OWNER и ADMIN.
        Если указан language (ru/en), возвращает только с совпадающим языком интерфейса.
        """
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
                if u.language and u.language.split("-")[0].lower() == lang_normalized
            ]
        logger.info(
            "Получено %d владельцев/админов (language=%s)",
            len(users),
            language,
        )
        return users

    @transactional
    async def get_user_by_username(
        self, session: AsyncSession, username: str
    ) -> Optional[User]:
        """Получает пользователя по имени пользователя (регистронезависимо)."""
        user = await self._fetch_user_one(
            session,
            func.lower(User.username) == func.lower(username),
        )
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

    @transactional
    async def create_user(
        self,
        session: AsyncSession,
        /,
        tg_id: Optional[str] = None,
        username: Optional[str] = None,
        role: Optional[UserRole] = UserRole.USER,
        language: str = "ru",
    ) -> User:
        """Создает нового пользователя."""
        if tg_id is None and username is None:
            raise ValueError("tg_id или username должны быть указаны")

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

    @transactional
    async def update_user_language(
        self, session: AsyncSession, user_id: int, language: str
    ) -> Optional[User]:
        """Обновляет язык пользователя."""
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

    @transactional
    async def update_user_role(
        self, session: AsyncSession, user_id: int, new_role: UserRole
    ) -> Optional[User]:
        """Обновляет роль пользователя."""
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

    @transactional
    async def delete_user(self, session: AsyncSession, /, user_id: int) -> bool:
        """Удаляет пользователя по его ID"""
        query = delete(User).where(User.id == user_id)
        result = await session.execute(query)
        await session.commit()

        deleted_count: int = getattr(result, "rowcount", 0) or 0
        if deleted_count > 0:
            logger.info("Удален пользователь с ID=%s", user_id)
            return True
        else:
            logger.warning(
                "Пользователь с ID=%s не найден для удаления",
                user_id,
            )
            return False
