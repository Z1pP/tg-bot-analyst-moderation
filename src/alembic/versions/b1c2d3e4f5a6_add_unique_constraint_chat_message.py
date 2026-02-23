"""Уникальное ограничение (chat_id, message_id) для chat_messages

Revision ID: b1c2d3e4f5a6
Revises: a2b3c4d5e6f7
Create Date: 2026-02-23 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, None] = "a2b3c4d5e6f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Удаляем дубли, оставляя строку с наименьшим id для каждой пары (chat_id, message_id)
    op.execute("""
        DELETE FROM chat_messages
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM chat_messages
            GROUP BY chat_id, message_id
        )
    """)
    op.create_unique_constraint(
        "uq_chat_message_chat_id_message_id",
        "chat_messages",
        ["chat_id", "message_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_chat_message_chat_id_message_id",
        "chat_messages",
        type_="unique",
    )
