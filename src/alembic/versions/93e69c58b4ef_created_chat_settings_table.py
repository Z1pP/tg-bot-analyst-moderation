"""created chat_settings table

Revision ID: 93e69c58b4ef
Revises: b71d8e70842f
Create Date: 2026-01-10 17:31:04.017864

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "93e69c58b4ef"
down_revision: Union[str, None] = "b71d8e70842f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Создаем таблицу chat_settings
    op.create_table(
        "chat_settings",
        sa.Column("chat_id", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("tolerance", sa.Integer(), nullable=False),
        sa.Column("is_antibot_enabled", sa.Boolean(), nullable=False),
        sa.Column("welcome_text", sa.String(length=4096), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["chat_id"], ["chat_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chat_id"),
    )

    # 2. ПЕРЕНОС ДАННЫХ: копируем существующие настройки из chat_sessions в новую таблицу
    op.execute("""
        INSERT INTO chat_settings (chat_id, start_time, end_time, tolerance, is_antibot_enabled, created_at)
        SELECT id, start_time, end_time, tolerance, is_antibot_enabled, now()
        FROM chat_sessions
    """)

    # 3. Удаляем старые колонки из chat_sessions
    op.drop_column("chat_sessions", "tolerance")
    op.drop_column("chat_sessions", "is_antibot_enabled")
    op.drop_column("chat_sessions", "end_time")
    op.drop_column("chat_sessions", "start_time")


def downgrade() -> None:
    """Downgrade schema."""
    # 1. Добавляем колонки обратно
    op.add_column("chat_sessions", sa.Column("start_time", sa.Time(), nullable=True))
    op.add_column("chat_sessions", sa.Column("end_time", sa.Time(), nullable=True))
    op.add_column(
        "chat_sessions", sa.Column("is_antibot_enabled", sa.Boolean(), nullable=True)
    )
    op.add_column("chat_sessions", sa.Column("tolerance", sa.Integer(), nullable=True))

    # 2. ПЕРЕНОС ДАННЫХ ОБРАТНО: возвращаем настройки из chat_settings в chat_sessions
    op.execute("""
        UPDATE chat_sessions
        SET start_time = cs.start_time,
            end_time = cs.end_time,
            is_antibot_enabled = cs.is_antibot_enabled,
            tolerance = cs.tolerance
        FROM chat_settings cs
        WHERE chat_sessions.id = cs.chat_id
    """)

    # 3. Делаем колонки обязательными (если они были такими)
    op.alter_column("chat_sessions", "start_time", nullable=False)
    op.alter_column("chat_sessions", "end_time", nullable=False)
    op.alter_column("chat_sessions", "is_antibot_enabled", nullable=False)
    op.alter_column("chat_sessions", "tolerance", nullable=False)

    # 4. Удаляем таблицу настроек
    op.drop_table("chat_settings")
