import logging
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import and_, func, select
from sqlalchemy.exc import SQLAlchemyError

from constants.enums import MembershipEventType
from exceptions import DatabaseException
from models import ChatMembershipEvent
from repositories.base import BaseRepository

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MembershipEventCounts:
    """Количество событий состава чата за период по типам."""

    joins: int
    left_count: int
    removed_count: int


class ChatMembershipEventRepository(BaseRepository):
    """Репозиторий событий вступления и ухода участников чата."""

    async def add(
        self,
        *,
        chat_id: int,
        user_tgid: int,
        event_type: MembershipEventType,
    ) -> None:
        async with self._db.session() as session:
            try:
                event = ChatMembershipEvent(
                    chat_id=chat_id,
                    user_tgid=user_tgid,
                    event_type=event_type.value,
                )
                session.add(event)
                await session.commit()
                logger.info(
                    "Записано событие состава чата: chat_id=%s user_tgid=%s type=%s",
                    chat_id,
                    user_tgid,
                    event_type.value,
                )
            except SQLAlchemyError as e:
                logger.error(
                    "Ошибка записи события состава чата: %s",
                    e,
                    exc_info=True,
                )
                await session.rollback()
                raise DatabaseException(
                    details={"context": "chat_membership_event_add", "original": str(e)}
                ) from e

    async def count_by_chat_and_period(
        self,
        *,
        chat_id: int,
        start_date: datetime,
        end_date: datetime,
    ) -> MembershipEventCounts:
        async with self._db.session() as session:
            try:
                stmt = (
                    select(
                        ChatMembershipEvent.event_type,
                        func.count(ChatMembershipEvent.id),
                    )
                    .where(
                        and_(
                            ChatMembershipEvent.chat_id == chat_id,
                            ChatMembershipEvent.created_at.between(
                                start_date,
                                end_date,
                            ),
                        )
                    )
                    .group_by(ChatMembershipEvent.event_type)
                )
                result = await session.execute(stmt)
                rows = list(result.all())
                counts_map = {row[0]: int(row[1]) for row in rows}
                return MembershipEventCounts(
                    joins=counts_map.get(MembershipEventType.JOIN.value, 0),
                    left_count=counts_map.get(MembershipEventType.LEFT.value, 0),
                    removed_count=counts_map.get(MembershipEventType.REMOVED.value, 0),
                )
            except SQLAlchemyError as e:
                logger.error(
                    "Ошибка подсчёта событий состава чата: %s",
                    e,
                    exc_info=True,
                )
                await session.rollback()
                raise DatabaseException(
                    details={
                        "context": "count_by_chat_and_period",
                        "original": str(e),
                    }
                ) from e
