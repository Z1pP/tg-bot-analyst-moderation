import logging
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from constants.enums import MembershipEventType
from models import ChatMembershipEvent
from repositories.base import BaseRepository, transactional

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MembershipEventCounts:
    """Количество событий состава чата за период по типам."""

    joins: int
    left_count: int
    removed_count: int


class ChatMembershipEventRepository(BaseRepository):
    """Репозиторий событий вступления и ухода участников чата."""

    @transactional
    async def add(
        self,
        session: AsyncSession,
        /,
        *,
        chat_id: int,
        user_tgid: int,
        event_type: MembershipEventType,
    ) -> None:
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

    @transactional
    async def count_by_chat_and_period(
        self,
        session: AsyncSession,
        /,
        *,
        chat_id: int,
        start_date: datetime,
        end_date: datetime,
    ) -> MembershipEventCounts:
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
