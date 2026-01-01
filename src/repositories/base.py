import logging
from typing import Any, List, Type, TypeVar

from sqlalchemy.dialects.postgresql import insert

from database.session import DatabaseContextManager

T = TypeVar("T")
logger = logging.getLogger(__name__)


class BaseRepository:
    def __init__(self, db_manager: DatabaseContextManager) -> None:
        self._db = db_manager

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
                stmt = insert(model.__table__).values(mappings).on_conflict_do_nothing()

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
            except Exception as e:
                logger.error(
                    "Ошибка при массовом добавлении %s: %s", label, e, exc_info=True
                )
                await session.rollback()
                return 0
