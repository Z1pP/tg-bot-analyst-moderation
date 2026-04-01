"""Таблица событий вступления и ухода участников чата.

Revision ID: c8e9f0a1b2c3
Revises: b1c2d3e4f5a6
Create Date: 2026-04-01 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c8e9f0a1b2c3"
down_revision: Union[str, None] = "b1c2d3e4f5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "chat_membership_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column("chat_id", sa.Integer(), nullable=False),
        sa.Column("user_tgid", sa.BigInteger(), nullable=False),
        sa.Column("event_type", sa.String(length=16), nullable=False),
        sa.ForeignKeyConstraint(
            ["chat_id"],
            ["chat_sessions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_chat_membership_events_chat_created",
        "chat_membership_events",
        ["chat_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "idx_chat_membership_events_chat_created",
        table_name="chat_membership_events",
    )
    op.drop_table("chat_membership_events")
