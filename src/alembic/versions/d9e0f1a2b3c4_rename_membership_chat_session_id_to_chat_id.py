"""Переименование chat_session_id -> chat_id в chat_membership_events (совместимость).

Revision ID: d9e0f1a2b3c4
Revises: c8e9f0a1b2c3
Create Date: 2026-04-01 14:00:00.000000

Если таблица создана старой ревизией c8e9 с колонкой chat_session_id,
переименовываем в chat_id и индекс. Свежая c8e9 уже создаёт chat_id — шаг no-op.


"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d9e0f1a2b3c4"
down_revision: Union[str, None] = "c8e9f0a1b2c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if not insp.has_table("chat_membership_events"):
        return
    cols = {c["name"] for c in insp.get_columns("chat_membership_events")}
    if "chat_session_id" not in cols:
        return
    op.drop_index(
        "idx_chat_membership_events_session_created",
        table_name="chat_membership_events",
        if_exists=True,
    )
    op.alter_column(
        "chat_membership_events",
        "chat_session_id",
        new_column_name="chat_id",
        existing_type=sa.Integer(),
        existing_nullable=False,
    )
    op.create_index(
        "idx_chat_membership_events_chat_created",
        "chat_membership_events",
        ["chat_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Откат не реализован: после upgrade нельзя отличить БД «переименовали» от «создали chat_id сразу»."""
    pass
