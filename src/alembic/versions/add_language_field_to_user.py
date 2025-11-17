"""add language field to user

Revision ID: a1b2c3d4e5f6
Revises: c4e39a60309a
Create Date: 2025-01-16 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "c4e39a60309a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Добавляем колонку language в таблицу users
    op.add_column(
        "users",
        sa.Column(
            "language", sa.String(length=10), nullable=False, server_default="ru"
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Удаляем колонку language из таблицы users
    op.drop_column("users", "language")
