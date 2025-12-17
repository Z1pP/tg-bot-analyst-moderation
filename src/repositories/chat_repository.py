import logging
from datetime import time
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database.session import DatabaseContextManager
from models.chat_session import ChatSession

logger = logging.getLogger(__name__)


class ChatRepository:
    def __init__(self, db_manager: DatabaseContextManager) -> None:
        self._db = db_manager

    async def get_chat_by_id(self, chat_id: int) -> Optional[ChatSession]:
        """Получает чат по идентификатору."""
        async with self._db.session() as session:
            try:
                chat = await session.scalar(
                    select(ChatSession)
                    .where(ChatSession.id == chat_id)
                    .options(
                        selectinload(ChatSession.archive_chat),
                    )
                )
                if chat:
                    # Явно загружаем archive_chat до выхода из сессии
                    _ = chat.archive_chat
                    # Отсоединяем объект от сессии, но сохраняем загруженные данные
                    session.expunge(chat)
                    if chat.archive_chat:
                        session.expunge(chat.archive_chat)
                    logger.info(
                        "Получен чат: chat_id=%s, title=%s",
                        chat.id,
                        chat.title,
                    )
                else:
                    logger.info("Чат не найден: id=%s", chat_id)
                return chat
            except Exception as e:
                logger.error("Произошла ошибка при получении чата: %s, %s", chat_id, e)
                raise e

    async def get_chat_by_tgid(self, chat_tgid: str) -> Optional[ChatSession]:
        """Получает чат по Telegram chat_id."""
        async with self._db.session() as session:
            try:
                chat = await session.scalar(
                    select(ChatSession)
                    .where(ChatSession.chat_id == chat_tgid)
                    .options(
                        selectinload(ChatSession.archive_chat),
                    )
                )
                if chat:
                    # Явно загружаем archive_chat до выхода из сессии
                    _ = chat.archive_chat
                    # Отсоединяем объект от сессии, но сохраняем загруженные данные
                    session.expunge(chat)
                    if chat.archive_chat:
                        session.expunge(chat.archive_chat)
                    logger.info(
                        "Получен чат: chat_id=%s, title=%s",
                        chat.chat_id,
                        chat.title,
                    )
                else:
                    logger.info("Чат не найден: chat_id=%s", chat_tgid)
                return chat
            except Exception as e:
                logger.error(
                    "Произошла ошибка при получении чата: %s, %s", chat_tgid, e
                )
                raise e

    async def get_all(self) -> List[ChatSession]:
        """Получает список всех чатов."""
        async with self._db.session() as session:
            try:
                result = await session.execute(select(ChatSession))
                chats = result.scalars().all()
                logger.info("Получено %d чатов", len(chats))
                return chats
            except Exception as e:
                logger.error("Произошла ошибка при получении всех чатов: %s", e)
                raise e

    async def get_chats_with_archive(self) -> List[ChatSession]:
        """Получает список чатов, у которых есть архивные чаты."""
        async with self._db.session() as session:
            try:
                result = await session.execute(
                    select(ChatSession)
                    .where(ChatSession.archive_chat_id.isnot(None))
                    .options(selectinload(ChatSession.archive_chat))
                )
                chats = result.scalars().all()

                logger.info("Получено %d чатов с архивными чатами", len(chats))
                return chats
            except Exception as e:
                logger.error(
                    "Произошла ошибка при получении чатов с архивными чатами: %s", e
                )
                raise e

    async def create_chat(self, chat_id: str, title: str) -> ChatSession:
        """Создает новый чат."""
        async with self._db.session() as session:
            try:
                chat = ChatSession(
                    chat_id=chat_id,
                    title=title,
                )
                session.add(chat)
                await session.commit()
                await session.refresh(chat)
                logger.info("Создан новый чат: chat_id=%s, title=%s", chat_id, title)
                return chat
            except Exception as e:
                logger.error("Произошла ошибка при создании чата: %s, %s", chat_id, e)
                await session.rollback()
                raise e

    async def update_chat(self, chat_id: int, title: str) -> ChatSession:
        """Обновляет название чата."""
        async with self._db.session() as session:
            try:
                chat = await session.get(ChatSession, chat_id)
                if chat:
                    chat.title = title
                    await session.commit()
                    await session.refresh(chat)
                    logger.info(
                        "Обновлен чат: chat_id=%s, new_title=%s", chat_id, title
                    )
                    return chat
                else:
                    logger.error("Чат не найден для обновления: chat_id=%s", chat_id)
                    raise ValueError(f"Чат с id {chat_id} не найден")
            except Exception as e:
                logger.error("Произошла ошибка при обновлении чата: %s, %s", chat_id, e)
                await session.rollback()
                raise e

    async def get_tracked_chats_for_admin(self, admin_tg_id: int) -> List[ChatSession]:
        """Получает отслеживаемые чаты для администратора"""
        async with self._db.session() as session:
            try:
                # Предполагаем, что все чаты отслеживаются для всех админов
                # В реальности здесь должна быть связь admin -> tracked_chats
                result = await session.execute(select(ChatSession))
                chats = result.scalars().all()
                logger.info(
                    f"Получено {len(chats)} отслеживаемых чатов для admin {admin_tg_id}"
                )
                return chats
            except Exception as e:
                logger.error(
                    f"Error getting tracked chats for admin {admin_tg_id}: {e}"
                )
                return []

    async def bind_archive_chat(
        self,
        work_chat_id: int,
        archive_chat_tgid: str,
        archive_chat_title: Optional[str] = None,
    ) -> Optional[ChatSession]:
        """
        Привязывает архивный чат к рабочему.

        Args:
            work_chat_id: ID рабочего чата из БД
            archive_chat_tgid: Telegram ID архивного чата
            archive_chat_title: Название архивного чата (опционально)

        Returns:
            Обновленный рабочий чат или None если рабочий чат не найден
        """
        async with self._db.session() as session:
            try:
                # Получаем рабочий чат с загрузкой archive_chat
                work_chat = await session.scalar(
                    select(ChatSession)
                    .where(ChatSession.id == work_chat_id)
                    .options(
                        selectinload(ChatSession.archive_chat),
                    )
                )
                if not work_chat:
                    logger.error("Рабочий чат не найден: id=%s", work_chat_id)
                    return None

                # Получаем или создаем архивный чат
                archive_chat = await self.get_chat_by_tgid(archive_chat_tgid)
                if not archive_chat:
                    # Создаем новый архивный чат
                    if not archive_chat_title:
                        archive_chat_title = f"Архивный чат {archive_chat_tgid}"
                    archive_chat = await self.create_chat(
                        chat_id=archive_chat_tgid, title=archive_chat_title
                    )
                    logger.info(
                        "Создан новый архивный чат: chat_id=%s, title=%s",
                        archive_chat_tgid,
                        archive_chat_title,
                    )

                # Обновляем привязку
                work_chat.archive_chat_id = archive_chat.chat_id
                await session.commit()
                # Перезагружаем с selectinload для archive_chat
                work_chat = await session.scalar(
                    select(ChatSession)
                    .where(ChatSession.id == work_chat_id)
                    .options(
                        selectinload(ChatSession.archive_chat),
                    )
                )
                # Явно загружаем archive_chat до выхода из сессии
                _ = work_chat.archive_chat
                # Отсоединяем объект от сессии, но сохраняем загруженные данные
                session.expunge(work_chat)
                if work_chat.archive_chat:
                    session.expunge(work_chat.archive_chat)

                logger.info(
                    "Архивный чат %s привязан к рабочему чату %s",
                    archive_chat_tgid,
                    work_chat_id,
                )

                return work_chat

            except Exception as e:
                logger.error(
                    "Ошибка при привязке архивного чата: work_chat_id=%s, archive_chat_tgid=%s, error=%s",
                    work_chat_id,
                    archive_chat_tgid,
                    e,
                )
                await session.rollback()
                raise e

    async def update_work_hours(
        self,
        chat_id: int,
        start_time: Optional[time] = None,
        end_time: Optional[time] = None,
        tolerance: Optional[int] = None,
    ) -> Optional[ChatSession]:
        """
        Обновляет рабочие часы чата для фильтрации данных в отчетах.

        Args:
            chat_id: ID чата из БД
            start_time: Время начала рабочего дня (опционально)
            end_time: Время конца рабочего дня (опционально)
            tolerance: Допустимое отклонение в минутах (опционально)

        Returns:
            Обновленный чат или None если чат не найден
        """
        async with self._db.session() as session:
            try:
                chat = await session.get(ChatSession, chat_id)
                if not chat:
                    logger.error(
                        "Чат не найден для обновления рабочих часов: chat_id=%s",
                        chat_id,
                    )
                    return None

                if start_time is not None:
                    chat.start_time = start_time
                if end_time is not None:
                    chat.end_time = end_time
                if tolerance is not None:
                    chat.tolerance = tolerance

                await session.commit()
                await session.refresh(chat)
                logger.info(
                    "Обновлены рабочие часы чата: chat_id=%s, start_time=%s, end_time=%s, tolerance=%s",
                    chat_id,
                    start_time,
                    end_time,
                    tolerance,
                )
                return chat
            except Exception as e:
                logger.error(
                    "Ошибка при обновлении рабочих часов чата: chat_id=%s, %s",
                    chat_id,
                    e,
                )
                await session.rollback()
                raise e
