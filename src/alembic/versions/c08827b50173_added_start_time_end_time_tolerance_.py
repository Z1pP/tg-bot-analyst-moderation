"""added start_time end_time tolerance fields to chat_sessions table

Revision ID: c08827b50173
Revises: 981d540d991f
Create Date: 2025-12-17 01:30:56.642795

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy import text

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c08827b50173"
down_revision: Union[str, None] = "981d540d991f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add columns as nullable first
    op.add_column("chat_sessions", sa.Column("start_time", sa.Time(), nullable=True))
    op.add_column("chat_sessions", sa.Column("end_time", sa.Time(), nullable=True))
    op.add_column("chat_sessions", sa.Column("tolerance", sa.Integer(), nullable=True))

    # Set default values for existing rows (using constants from work_time)
    # Default: start_time = 10:00, end_time = 22:00, tolerance = 10 minutes
    op.execute(
        text(
            "UPDATE chat_sessions SET start_time = '10:00:00' WHERE start_time IS NULL"
        )
    )
    op.execute(
        text("UPDATE chat_sessions SET end_time = '22:00:00' WHERE end_time IS NULL")
    )
    op.execute(text("UPDATE chat_sessions SET tolerance = 10 WHERE tolerance IS NULL"))

    # Now make them NOT NULL (optional - only if you want to enforce it)
    op.alter_column("chat_sessions", "start_time", nullable=False)
    op.alter_column("chat_sessions", "end_time", nullable=False)
    op.alter_column("chat_sessions", "tolerance", nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("chat_sessions", "tolerance")
    op.drop_column("chat_sessions", "end_time")
    op.drop_column("chat_sessions", "start_time")
