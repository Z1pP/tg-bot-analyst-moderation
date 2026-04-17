import logging
from datetime import time
from typing import Any, Callable, List, Optional, cast

import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from exceptions import DatabaseException
from models import ChatSession, ChatSettings
from repositories.base import BaseRepository

logger = logging.getLogger(__name__)


def _chat_select_with_relations() -> Any:
    """Общий запрос чата с загрузкой archive_chat и settings."""
    return select(ChatSession).options(
        selectinload(ChatSession.archive_chat),
        selectinload(ChatSession.settings),
    )


class ChatRepository(BaseRepository):
    async def _get_chat_by_criteria(
        self,
        session: Any,
        where_clause: Any,
        not_found_log_value: Any,
        success_log_attr: str,
    ) -> Optional[ChatSession]:
        """Получает чат по критерию с загрузкой archive_chat и settings. Для внутреннего использования."""
        chat = cast(
            Optional[ChatSession],
            await session.scalar(_chat_select_with_relations().where(where_clause)),
        )
        if chat:
            self._expunge_chat_with_archive(session, chat)
            logger.info(
                "Получен чат: chat_id=%s, title=%s",
                getattr(chat, success_log_attr),
                chat.title,
            )
        else:
            logger.info("Чат не найден: %s", not_found_log_value)
        return chat

    async def get_chat_by_id(self, chat_id: int) -> Optional[ChatSession]:
        """Получает чат по идентификатору."""
        async with self._db.session() as session:
            try:
                return await self._get_chat_by_criteria(
                    session,
                    ChatSession.id == chat_id,
                    chat_id,
                    "id",
                )
            except SQLAlchemyError as e:
                logger.error(
                    "Произошла ошибка при получении чата: %s, %s",
                    chat_id,
                    e,
                    exc_info=True,
                )
                await session.rollback()
                raise DatabaseException(
                    details={"context": "get_chat_by_id", "original": str(e)}
                ) from e

    async def get_chat_by_tgid(self, chat_tgid: str) -> Optional[ChatSession]:
        """Получает чат по Telegram chat_id."""
        async with self._db.session() as session:
            try:
                return await self._get_chat_by_criteria(
                    session,
                    ChatSession.chat_id == chat_tgid,
                    chat_tgid,
                    "chat_id",
                )
            except SQLAlchemyError as e:
                logger.error(
                    "Произошла ошибка при получении чата: %s, %s",
                    chat_tgid,
                    e,
                    exc_info=True,
                )
                await session.rollback()
                raise DatabaseException(
                    details={"context": "get_chat_by_tgid", "original": str(e)}
                ) from e

    async def _get_chat_with_settings_for_update(
        self, session: Any, chat_id: int
    ) -> Optional[tuple[ChatSession, ChatSettings]]:
        """
        Загружает чат с настройками и при отсутствии создаёт ChatSettings.
        Для использования в методах обновления/переключения настроек чата.
        """
        chat = await session.scalar(
            select(ChatSession)
            .where(ChatSession.id == chat_id)
            .options(selectinload(ChatSession.settings))
        )
        if not chat:
            return None
        if not chat.settings:
            chat.settings = ChatSettings(chat_id=chat.id)
            session.add(chat.settings)
        return (chat, chat.settings)

    async def get_all(self) -> List[ChatSession]:
        """Получает список всех чатов."""
        async with self._db.session() as session:
            try:
                result = await session.execute(
                    select(ChatSession).options(selectinload(ChatSession.settings))
                )
                chats = list(result.scalars().all())

                # Убеждаемся, что настройки подгружены
                for chat in chats:
                    _ = chat.settings

                session.expunge_all()

                logger.info("Получено %d чатов", len(chats))
                return chats
            except SQLAlchemyError as e:
                logger.error(
                    "Произошла ошибка при получении всех чатов: %s",
                    e,
                    exc_info=True,
                )
                await session.rollback()
                raise DatabaseException(
                    details={"context": "get_all", "original": str(e)}
                ) from e

    async def create_chat(self, chat_id: str, title: str) -> ChatSession:
        """Создает новый чат."""
        async with self._db.session() as session:
            try:
                chat = ChatSession(
                    chat_id=chat_id,
                    title=title,
                )
                session.add(chat)

                await session.flush()

                settings = ChatSettings(
                    chat_id=chat.id,
                )
                session.add(settings)

                await session.commit()
                await session.refresh(chat)
                self._expunge_chat_with_archive(session, chat)

                logger.info(
                    "Создан новый чат и его настройки: chat_id=%s, title=%s",
                    chat_id,
                    title,
                )
                return chat
            except SQLAlchemyError as e:
                logger.error(
                    "Произошла ошибка при создании чата: %s, %s",
                    chat_id,
                    e,
                    exc_info=True,
                )
                await session.rollback()
                raise DatabaseException(
                    details={"context": "create_chat", "original": str(e)}
                ) from e

    async def update_chat(self, chat_id: int, title: str) -> ChatSession:
        """Обновляет название чата."""
        async with self._db.session() as session:
            try:
                chat = await session.get(ChatSession, chat_id)
                if chat:
                    chat.title = title
                    await session.commit()
                    await session.refresh(chat)
                    self._expunge_chat_with_archive(session, chat)
                    logger.info(
                        "Обновлен чат: chat_id=%s, new_title=%s", chat_id, title
                    )
                    return chat
                else:
                    logger.error("Чат не найден для обновления: chat_id=%s", chat_id)
                    raise ValueError(f"Чат с id {chat_id} не найден")
            except SQLAlchemyError as e:
                logger.error(
                    "Произошла ошибка при обновлении чата: %s, %s",
                    chat_id,
                    e,
                    exc_info=True,
                )
                await session.rollback()
                raise DatabaseException(
                    details={"context": "update_chat", "original": str(e)}
                ) from e

    async def get_tracked_chats_for_admin(self, admin_tg_id: int) -> List[ChatSession]:
        """Получает отслеживаемые чаты для администратора"""
        async with self._db.session() as session:
            try:
                # Предполагаем, что все чаты отслеживаются для всех админов
                # В реальности здесь должна быть связь admin -> tracked_chats
                result = await session.execute(
                    select(ChatSession).options(selectinload(ChatSession.settings))
                )
                chats = list(result.scalars().all())

                for chat in chats:
                    _ = chat.settings

                session.expunge_all()

                logger.info(
                    "Получено %d отслеживаемых чатов для admin %s",
                    len(chats),
                    admin_tg_id,
                )
                return chats
            except SQLAlchemyError as e:
                logger.error(
                    "Ошибка при получении отслеживаемых чатов для admin %s: %s",
                    admin_tg_id,
                    e,
                    exc_info=True,
                )
                await session.rollback()
                raise DatabaseException(
                    details={
                        "context": "get_tracked_chats_for_admin",
                        "original": str(e),
                    }
                ) from e

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
                # Перезагружаем с selectinload для archive_chat и settings
                work_chat = await session.scalar(
                    select(ChatSession)
                    .where(ChatSession.id == work_chat_id)
                    .options(
                        selectinload(ChatSession.archive_chat),
                        selectinload(ChatSession.settings),
                    )
                )
                self._expunge_chat_with_archive(session, work_chat)

                logger.info(
                    "Архивный чат %s привязан к рабочему чату %s",
                    archive_chat_tgid,
                    work_chat_id,
                )

                return cast(ChatSession, work_chat)

            except SQLAlchemyError as e:
                logger.error(
                    "Ошибка при привязке архивного чата: work_chat_id=%s, archive_chat_tgid=%s, error=%s",
                    work_chat_id,
                    archive_chat_tgid,
                    e,
                    exc_info=True,
                )
                await session.rollback()
                raise DatabaseException(
                    details={"context": "bind_archive_chat", "original": str(e)}
                ) from e

    async def update_work_hours(
        self,
        chat_id: int,
        start_time: Optional[time] = None,
        end_time: Optional[time] = None,
        tolerance: Optional[int] = None,
        breaks_time: Optional[int] = None,
    ) -> Optional[ChatSession]:
        """
        Обновляет рабочие часы чата для фильтрации данных в отчетах.

        Args:
            chat_id: ID чата из БД
            start_time: Время начала рабочего дня (опционально)
            end_time: Время конца рабочего дня (опционально)
            tolerance: Допустимое отклонение в минутах (опционально)
            breaks_time: Интервал паузы в минутах (опционально)

        Returns:
            Обновленный чат или None если чат не найден
        """
        async with self._db.session() as session:
            try:
                chat = await session.scalar(
                    select(ChatSession)
                    .where(ChatSession.id == chat_id)
                    .options(selectinload(ChatSession.settings))
                )
                if not chat:
                    logger.error(
                        "Чат не найден для обновления рабочих часов: chat_id=%s",
                        chat_id,
                    )
                    return None

                if not chat.settings:
                    chat.settings = ChatSettings(chat_id=chat.id)
                    session.add(chat.settings)

                if start_time is not None:
                    chat.settings.start_time = start_time
                if end_time is not None:
                    chat.settings.end_time = end_time
                if tolerance is not None:
                    chat.settings.tolerance = tolerance
                if breaks_time is not None:
                    chat.settings.breaks_time = breaks_time

                await session.commit()
                await session.refresh(chat)
                self._expunge_chat_with_archive(session, chat)

                logger.info(
                    "Обновлены рабочие часы чата: chat_id=%s, start_time=%s, end_time=%s, tolerance=%s, breaks_time=%s",
                    chat_id,
                    start_time,
                    end_time,
                    tolerance,
                    breaks_time,
                )
                return chat
            except SQLAlchemyError as e:
                logger.error(
                    "Ошибка при обновлении рабочих часов чата: chat_id=%s, %s",
                    chat_id,
                    e,
                    exc_info=True,
                )
                await session.rollback()
                raise DatabaseException(
                    details={"context": "update_work_hours", "original": str(e)}
                ) from e

    async def _toggle_chat_setting_boolean(
        self,
        session: AsyncSession,
        chat_id: int,
        settings_attr: str,
        not_found_log: str,
        success_log_fmt: str,
        value_getter: Callable[[ChatSession], Any],
    ) -> Optional[ChatSession]:
        """
        Общая логика переключения булевой настройки чата (получить чат с settings,
        инвертировать атрибут, commit, refresh, expunge, лог). При ошибке не ловит
        исключения — вызывающий код должен использовать session в try/except.
        """
        pair = await self._get_chat_with_settings_for_update(session, chat_id)
        if not pair:
            logger.error(not_found_log, chat_id)
            return None
        chat, settings = pair
        setattr(settings, settings_attr, not getattr(settings, settings_attr))
        await session.commit()
        await session.refresh(chat, ["settings"])
        self._expunge_chat_with_archive(session, chat)
        logger.info(
            success_log_fmt,
            chat.title,
            chat.chat_id,
            value_getter(chat),
        )
        return chat

    async def toggle_antibot(self, chat_id: int) -> Optional[ChatSession]:
        """
        Переключает статус антибота для чата.

        Args:
            chat_id: ID чата из БД

        Returns:
            Обновленный чат или None если чат не найден
        """
        async with self._db.session() as session:
            try:
                return await self._toggle_chat_setting_boolean(
                    session,
                    chat_id,
                    "is_antibot_enabled",
                    "Чат не найден для переключения антибота: id=%s",
                    "Антибот для чата %s (ID: %s) переключен в состояние: %s",
                    lambda c: c.is_antibot_enabled,
                )
            except SQLAlchemyError as e:
                logger.error(
                    "Ошибка при переключении антибота для чата %s: %s",
                    chat_id,
                    e,
                    exc_info=True,
                )
                await session.rollback()
                raise DatabaseException(
                    details={"context": "toggle_antibot", "original": str(e)}
                ) from e

    async def toggle_auto_moderation(self, chat_id: int) -> Optional[ChatSession]:
        """
        Переключает автомодерацию (LLM-батч) для чата.

        Args:
            chat_id: ID чата из БД

        Returns:
            Обновлённый чат или None если чат не найден
        """
        async with self._db.session() as session:
            try:
                return await self._toggle_chat_setting_boolean(
                    session,
                    chat_id,
                    "is_auto_moderation_enabled",
                    "Чат не найден для переключения автомодерации: id=%s",
                    "Автомодерация для чата %s (ID: %s) переключена в состояние: %s",
                    lambda c: c.is_auto_moderation_enabled,
                )
            except SQLAlchemyError as e:
                logger.error(
                    "Ошибка при переключении автомодерации для чата %s: %s",
                    chat_id,
                    e,
                    exc_info=True,
                )
                await session.rollback()
                raise DatabaseException(
                    details={"context": "toggle_auto_moderation", "original": str(e)}
                ) from e

    async def toggle_show_welcome_text(self, chat_id: int) -> Optional[ChatSession]:
        """
        Переключает показ приветственного текста для чата.

        Args:
            chat_id: ID чата из БД

        Returns:
            Обновленный чат или None если чат не найден
        """
        async with self._db.session() as session:
            try:
                return await self._toggle_chat_setting_boolean(
                    session,
                    chat_id,
                    "show_welcome_text",
                    "Чат не найден для переключения приветствия: id=%s",
                    "Приветствие для чата %s (ID: %s) переключено в состояние: %s",
                    lambda c: c.settings.show_welcome_text,
                )
            except SQLAlchemyError as e:
                logger.error(
                    "Ошибка при переключении приветствия для чата %s: %s",
                    chat_id,
                    e,
                    exc_info=True,
                )
                await session.rollback()
                raise DatabaseException(
                    details={"context": "toggle_show_welcome_text", "original": str(e)}
                ) from e

    async def toggle_auto_delete_welcome_text(
        self, chat_id: int
    ) -> Optional[ChatSession]:
        """
        Переключает автоудаление приветственного текста для чата.

        Args:
            chat_id: ID чата из БД

        Returns:
            Обновленный чат или None если чат не найден
        """
        async with self._db.session() as session:
            try:
                return await self._toggle_chat_setting_boolean(
                    session,
                    chat_id,
                    "auto_delete_welcome_text",
                    "Чат не найден для переключения автоудаления: id=%s",
                    "Автоудаление приветствия для чата %s (ID: %s) переключено в состояние: %s",
                    lambda c: c.settings.auto_delete_welcome_text,
                )
            except SQLAlchemyError as e:
                logger.error(
                    "Ошибка при переключении автоудаления для чата %s: %s",
                    chat_id,
                    e,
                    exc_info=True,
                )
                await session.rollback()
                raise DatabaseException(
                    details={
                        "context": "toggle_auto_delete_welcome_text",
                        "original": str(e),
                    }
                ) from e

    async def update_welcome_text(
        self, chat_id: int, welcome_text: str
    ) -> Optional[ChatSession]:
        """
        Обновляет приветственный текст чата.

        Args:
            chat_id: ID чата из БД
            welcome_text: Новый текст приветствия

        Returns:
            Обновленный чат или None если чат не найден
        """
        async with self._db.session() as session:
            try:
                chat = await session.scalar(
                    select(ChatSession)
                    .where(ChatSession.id == chat_id)
                    .options(selectinload(ChatSession.settings))
                )
                if not chat:
                    logger.error(
                        "Чат не найден для обновления приветственного текста: chat_id=%s",
                        chat_id,
                    )
                    return None

                if not chat.settings:
                    chat.settings = ChatSettings(chat_id=chat.id)
                    session.add(chat.settings)

                chat.settings.welcome_text = welcome_text

                await session.commit()
                await session.refresh(chat)
                self._expunge_chat_with_archive(session, chat)

                logger.info(
                    "Обновлен приветственный текст чата: chat_id=%s",
                    chat_id,
                )
                return chat
            except SQLAlchemyError as e:
                logger.error(
                    "Ошибка при обновлении приветственного текста чата: chat_id=%s, %s",
                    chat_id,
                    e,
                    exc_info=True,
                )
                await session.rollback()
                raise DatabaseException(
                    details={"context": "update_welcome_text", "original": str(e)}
                ) from e

    def _expunge_chat_with_archive(
        self, session: AsyncSession, chat: ChatSession
    ) -> None:
        """Вспомогательный метод для отсоединения чата и его архива от сессии."""
        if not chat:
            return

        # Загружаем в память, если еще нет (через dict для безопасности в async)
        loaded_archive = chat.__dict__.get("archive_chat")
        loaded_settings = chat.__dict__.get("settings")

        # Отсоединяем только те объекты, которые реально есть в текущей сессии
        for obj in [chat, loaded_archive, loaded_settings]:
            if obj and obj != sa.orm.base.LoaderCallableStatus.NO_VALUE:
                try:
                    session.expunge(obj)
                except (sa.exc.InvalidRequestError, KeyError):
                    # Объект уже отсутствует в сессии - игнорируем
                    pass
