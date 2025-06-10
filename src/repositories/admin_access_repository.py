import logging
from typing import Optional

from sqlalchemy import select

from database.session import async_session
from models import AdminChatAccess, ChatSession

logger = logging.getLogger(__name__)


class AdminChatAccessRepository:
    async def get_admin_source_chats(self, admin_id: int) -> list[ChatSession]:
        """Получает список чатов-источников для администратора."""
        async with async_session() as session:
            try:
                query = (
                    select(ChatSession)
                    .join(AdminChatAccess)
                    .where(
                        AdminChatAccess.admin_id == admin_id,
                        AdminChatAccess.is_source,
                    )
                )
                result = await session.execute(query)
                chats = result.scalars().all()

                logger.info(
                    "Получено %d чатов-источников для администратора: %s",
                    len(chats),
                    admin_id,
                )
                return chats
            except Exception as e:
                logger.error("Произошла ошибка при получении чатов-источников: %s", e)
                raise e

    async def get_admin_target_chats(self, admin_id: int) -> list[ChatSession]:
        """Получает список чатов-получателей для администратора."""
        async with async_session() as session:
            try:
                query = (
                    select(ChatSession)
                    .join(AdminChatAccess)
                    .where(
                        AdminChatAccess.admin_id == admin_id,
                        AdminChatAccess.is_target,
                    )
                )
                result = await session.execute(query)
                chats = result.scalars().all()

                logger.info(
                    "Получено %d чатов-получателей для администратора: %s",
                    len(chats),
                    admin_id,
                )
                return chats
            except Exception as e:
                logger.error("Произошла ошибка при получении чатов-получателей: %s", e)
                raise e

    async def add_chat_access(
        self,
        admin_id: int,
        chat_id: int,
        is_source: bool = True,
        is_target: bool = False,
    ) -> Optional[AdminChatAccess]:
        """Добавляет доступ к чату для администратора."""
        async with async_session() as session:
            try:
                chat_access = AdminChatAccess(
                    admin_id=admin_id,
                    chat_id=chat_id,
                    is_source=is_source,
                    is_target=is_target,
                )
                session.add(chat_access)
                await session.commit()
                await session.refresh(chat_access)
                logger.info(
                    "Добавлен доступ к чату для администратора: admin_id=%s, chat_id=%s",
                    admin_id,
                    chat_id,
                )
                return chat_access
            except Exception as e:
                logger.error("Произошла ошибка при добавлении доступа к чату: %s", e)
                await session.rollback()
                raise e

    async def remove_chat_access(
        self,
        admin_id: int,
        chat_id: int,
    ) -> None:
        """Удаляет доступ к чату для администратора."""
        async with async_session() as session:
            try:
                query = select(AdminChatAccess).where(
                    AdminChatAccess.admin_id == admin_id,
                    AdminChatAccess.chat_id == chat_id,
                )
                result = await session.execute(query)
                chat_access = result.scalars().first()

                if chat_access:
                    await session.delete(chat_access)
                    await session.commit()
                    logger.info(
                        "Удален доступ к чату для администратора: admin_id=%s, chat_id=%s",
                        admin_id,
                        chat_id,
                    )
                else:
                    logger.warning(
                        "Доступ к чату не найден для администратора: admin_id=%s, chat_id=%s",
                        admin_id,
                        chat_id,
                    )
            except Exception as e:
                logger.error("Произошла ошибка при удалении доступа к чату: %s", e)
                await session.rollback()
                raise e

    async def get_access(
        self,
        admin_id: int,
        chat_id: int,
    ) -> Optional[AdminChatAccess]:
        """Проверяет наличие доступа администратора к чату."""
        async with async_session() as session:
            try:
                query = select(AdminChatAccess).where(
                    AdminChatAccess.admin_id == admin_id,
                    AdminChatAccess.chat_id == chat_id,
                )
                result = await session.execute(query)
                access = result.scalars().first()

                if access:
                    logger.info(
                        "Найден доступ администратора к чату: admin_id=%s, chat_id=%s",
                        admin_id,
                        chat_id,
                    )
                else:
                    logger.info(
                        "Доступ администратора к чату не найден: admin_id=%s, chat_id=%s",
                        admin_id,
                        chat_id,
                    )

                return access
            except Exception as e:
                logger.error("Произошла ошибка при проверке доступа к чату: %s", e)
                return None

    async def get_all_admin_chats(self, admin_id: int) -> list[ChatSession]:
        """Получает все чаты администратора (и источники, и получатели)."""
        async with async_session() as session:
            try:
                query = (
                    select(ChatSession)
                    .join(AdminChatAccess)
                    .where(AdminChatAccess.admin_id == admin_id)
                    .distinct()
                )
                result = await session.execute(query)
                chats = result.scalars().all()

                logger.info(
                    "Получено %d чатов для администратора: %s", len(chats), admin_id
                )
                return chats
            except Exception as e:
                logger.error(
                    "Произошла ошибка при получении всех чатов администратора: %s", e
                )
                return []

    async def set_chat_as_source(
        self,
        admin_id: int,
        chat_id: int,
        is_source: bool = True,
    ) -> Optional[AdminChatAccess]:
        """Устанавливает чат как источник данных."""
        async with async_session() as session:
            try:
                # Проверяем, существует ли уже доступ
                query = select(AdminChatAccess).where(
                    AdminChatAccess.admin_id == admin_id,
                    AdminChatAccess.chat_id == chat_id,
                )
                result = await session.execute(query)
                access = result.scalars().first()

                if access:
                    # Обновляем существующий доступ
                    access.is_source = is_source
                    access.is_target = False
                    await session.commit()
                    await session.refresh(access)
                    logger.info(
                        "Обновлен статус источника для чата: admin_id=%s, chat_id=%s, is_source=%s",
                        admin_id,
                        chat_id,
                        is_source,
                    )
                else:
                    # Создаем новый доступ
                    access = AdminChatAccess(
                        admin_id=admin_id,
                        chat_id=chat_id,
                        is_source=is_source,
                        is_target=False,  # По умолчанию не является получателем
                    )
                    session.add(access)
                    await session.commit()
                    await session.refresh(access)
                    logger.info(
                        "Создан новый доступ с статусом источника: admin_id=%s, chat_id=%s, is_source=%s",
                        admin_id,
                        chat_id,
                        is_source,
                    )

                return access
            except Exception as e:
                logger.error(
                    "Произошла ошибка при установке статуса источника для чата: %s", e
                )
                await session.rollback()
                return None

    async def set_chat_as_target(
        self,
        admin_id: int,
        chat_id: int,
        is_target: bool = True,
    ) -> Optional[AdminChatAccess]:
        """Устанавливает чат как получатель отчетов."""
        async with async_session() as session:
            try:
                # Проверяем, существует ли уже доступ
                query = select(AdminChatAccess).where(
                    AdminChatAccess.admin_id == admin_id,
                    AdminChatAccess.chat_id == chat_id,
                )
                result = await session.execute(query)
                access = result.scalars().first()

                if access:
                    # Обновляем существующий доступ
                    access.is_target = is_target
                    access.is_source = False
                    await session.commit()
                    await session.refresh(access)
                    logger.info(
                        "Обновлен статус получателя для чата: admin_id=%s, chat_id=%s, is_target=%s",
                        admin_id,
                        chat_id,
                        is_target,
                    )
                else:
                    # Создаем новый доступ
                    access = AdminChatAccess(
                        admin_id=admin_id,
                        chat_id=chat_id,
                        is_source=False,  # По умолчанию не является источником
                        is_target=is_target,
                    )
                    session.add(access)
                    await session.commit()
                    await session.refresh(access)
                    logger.info(
                        "Создан новый доступ с статусом получателя: admin_id=%s, chat_id=%s, is_target=%s",
                        admin_id,
                        chat_id,
                        is_target,
                    )

                return access
            except Exception as e:
                logger.error(
                    "Произошла ошибка при установке статуса получателя для чата: %s", e
                )
                await session.rollback()
                return None
