"""add dev, root, owner roles

Revision ID: 9f3b2c7a1d8e
Revises: 81102062da65
Create Date: 2026-01-24 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9f3b2c7a1d8e"
down_revision: Union[str, None] = "81102062da65"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add new enum values in strict hierarchy order.
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_enum e
                JOIN pg_type t ON t.oid = e.enumtypid
                WHERE t.typname = 'userrole' AND e.enumlabel = 'DEV'
            ) THEN
                ALTER TYPE userrole ADD VALUE 'DEV' BEFORE 'ADMIN';
            END IF;

            IF NOT EXISTS (
                SELECT 1
                FROM pg_enum e
                JOIN pg_type t ON t.oid = e.enumtypid
                WHERE t.typname = 'userrole' AND e.enumlabel = 'ROOT'
            ) THEN
                ALTER TYPE userrole ADD VALUE 'ROOT' BEFORE 'ADMIN';
            END IF;

            IF NOT EXISTS (
                SELECT 1
                FROM pg_enum e
                JOIN pg_type t ON t.oid = e.enumtypid
                WHERE t.typname = 'userrole' AND e.enumlabel = 'OWNER'
            ) THEN
                ALTER TYPE userrole ADD VALUE 'OWNER' BEFORE 'ADMIN';
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    raise RuntimeError(
        "Downgrade is not supported for removing enum values. "
        "Remove values manually if absolutely necessary."
    )
