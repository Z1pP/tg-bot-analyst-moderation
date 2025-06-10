"""fix_admin_chat_access_foreign_key

Revision ID: f1362a28cec9
Revises: 56d2e2904420
Create Date: 2025-06-10 22:27:01.468275

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f1362a28cec9"
down_revision: Union[str, None] = "56d2e2904420"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "admin_chat_access",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("admin_id", sa.Integer(), nullable=False),
        sa.Column("chat_id", sa.Integer(), nullable=False),
        sa.Column("is_source", sa.Boolean(), nullable=False, default=True),
        sa.Column("is_target", sa.Boolean(), nullable=False, default=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["admin_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["chat_id"], ["chat_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_admin_chat_access_admin_id"),
        "admin_chat_access",
        ["admin_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_admin_chat_access_chat_id"),
        "admin_chat_access",
        ["chat_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_admin_chat_access_chat_id"), table_name="admin_chat_access")
    op.drop_index(op.f("ix_admin_chat_access_admin_id"), table_name="admin_chat_access")
    op.drop_table("admin_chat_access")
