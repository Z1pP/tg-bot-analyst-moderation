"""increase emoji column length in message_reactions

Revision ID: a2b3c4d5e6f7
Revises: 9f3b2c7a1d8e
Create Date: 2026-02-04 19:20:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a2b3c4d5e6f7"
down_revision: Union[str, None] = "9f3b2c7a1d8e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "message_reactions",
        "emoji",
        existing_type=sa.VARCHAR(length=10),
        type_=sa.String(length=64),
        existing_nullable=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "message_reactions",
        "emoji",
        existing_type=sa.String(length=64),
        type_=sa.VARCHAR(length=10),
        existing_nullable=False,
    )
