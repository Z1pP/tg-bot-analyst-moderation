from __future__ import annotations

import functools
import logging
from typing import (
    Any,
    Awaitable,
    Callable,
    Concatenate,
    List,
    Optional,
    ParamSpec,
    Type,
    TypeVar,
    cast,
)

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import DatabaseContextManager
from exceptions import DatabaseException
from models.base import Base

T = TypeVar("T", bound=Base)
Repo = TypeVar("Repo", bound="BaseRepository")
P = ParamSpec("P")
R = TypeVar("R")
logger = logging.getLogger(__name__)


def transactional(
    method: Callable[Concatenate[Repo, AsyncSession, P], Awaitable[R]],
) -> Callable[Concatenate[Repo, P], Awaitable[R]]:
    """
    Декоратор для автоматического управления транзакциями в методах репозитория.

    Оборачивает асинхронные методы, автоматически создавая сессию через self._db.session(),
    передавая её первым аргументом после self в декорируемый метод.

    Args:
        method: Асинхронный метод репозитория, принимающий session как первый аргумент после self

    Returns:
        Обернутый метод с автоматическим управлением транзакциями
    """

    @functools.wraps(method)
    async def wrapper(self: Repo, *args: P.args, **kwargs: P.kwargs) -> R:
        async with self._db.session() as session:
            try:
                result = await method(self, session, *args, **kwargs)
                await session.commit()
                return result
            except SQLAlchemyError as e:
                logger.error(
                    "Ошибка БД в методе %s: %s", method.__name__, e, exc_info=True
                )
                await session.rollback()
                raise DatabaseException(
                    details={
                        "context": f"repository.{method.__name__}",
                        "repository": self.__class__.__name__,
                        "original": str(e),
                    }
                ) from e

    return cast(Callable[Concatenate[Repo, P], Awaitable[R]], wrapper)


class BaseRepository:
    def __init__(self, db_manager: DatabaseContextManager) -> None:
        self._db = db_manager

    async def _get_one_by_field(
        self,
        session: AsyncSession,
        model: Type[T],
        field: str,
        value: Any,
    ) -> Optional[T]:
        """
        Получает одну запись по значению поля.

        Args:
            session: Активная сессия SQLAlchemy
            model: Класс модели SQLAlchemy
            field: Имя поля для фильтрации
            value: Значение для поиска

        Returns:
            Optional[T]: Найденный объект или None
        """
        column = getattr(model, field)
        stmt = select(model).where(column == value)
        result = await session.execute(stmt)
        return result.scalars().first()

    async def _get_all(
        self,
        session: AsyncSession,
        model: Type[T],
        order_by: Optional[str] = None,
    ) -> List[T]:
        """
        Получает все записи модели с опциональной сортировкой.

        Args:
            session: Активная сессия SQLAlchemy
            model: Класс модели SQLAlchemy
            order_by: Имя поля для сортировки (опционально)

        Returns:
            List[T]: Список всех объектов модели
        """
        stmt = select(model)

        if order_by is not None:
            column = getattr(model, order_by)
            stmt = stmt.order_by(column)

        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def _bulk_upsert_on_conflict_nothing(
        self,
        model: Type[T],
        mappings: List[dict[str, Any]],
        label: str = "записей",
    ) -> int:
        """
        Универсальный метод для массовой вставки с игнорированием конфликтов.

        Args:
            model: Класс модели SQLAlchemy
            mappings: Список словарей с данными для вставки
            label: Метка для логирования (например, "сообщений")

        Returns:
            int: Количество реально вставленных записей
        """
        if not mappings:
            return 0

        async with self._db.session() as session:
            try:
                # Используем PostgreSQL INSERT ... ON CONFLICT DO NOTHING
                stmt = insert(model.__table__).values(mappings).on_conflict_do_nothing()  # type: ignore[arg-type]

                result = await session.execute(stmt)
                await session.commit()

                # rowcount в PostgreSQL при ON CONFLICT DO NOTHING
                # возвращает количество реально вставленных строк
                inserted_count = (
                    result.rowcount if hasattr(result, "rowcount") else len(mappings)
                )

                logger.info(
                    "Массово добавлено %s: %d из %d",
                    label,
                    inserted_count,
                    len(mappings),
                )
                return inserted_count
            except SQLAlchemyError as e:
                logger.error(
                    "Ошибка при массовом добавлении %s: %s", label, e, exc_info=True
                )
                await session.rollback()
                raise DatabaseException(
                    details={"context": f"bulk_upsert_{label}", "original": str(e)}
                ) from e
