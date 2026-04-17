"""Добавление is_auto_moderation_enabled в chat_settings.

Revision ID: e7f8a9b0c1d2
Revises: d9e0f1a2b3c4
Create Date: 2026-04-17

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e7f8a9b0c1d2"
down_revision: Union[str, None] = "d9e0f1a2b3c4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "chat_settings",
        sa.Column(
            "is_auto_moderation_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.alter_column(
        "chat_settings",
        "is_auto_moderation_enabled",
        server_default=None,
    )


def downgrade() -> None:
    op.drop_column("chat_settings", "is_auto_moderation_enabled")
