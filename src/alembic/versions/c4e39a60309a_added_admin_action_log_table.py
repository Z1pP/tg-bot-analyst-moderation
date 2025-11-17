"""added admin action log table

Revision ID: c4e39a60309a
Revises: 19df38c2c82d
Create Date: 2025-11-14 06:11:21.029092

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4e39a60309a'
down_revision: Union[str, None] = '19df38c2c82d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()

    # Проверяем, существует ли таблица
    table_exists = conn.execute(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
            "WHERE table_name = 'admin_action_logs')"
        )
    ).scalar()

    # Проверяем, существует ли enum (для удаления, если есть)
    enum_exists = conn.execute(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'adminactiontype')"
        )
    ).scalar()

    # Если enum существует и таблица тоже существует, нужно изменить тип колонки
    if enum_exists and table_exists:
        # Изменяем тип колонки с enum на VARCHAR
        op.execute("ALTER TABLE admin_action_logs ALTER COLUMN action_type TYPE VARCHAR(50) USING action_type::text")
        # Удаляем enum, так как больше не используется
        op.execute("DROP TYPE IF EXISTS adminactiontype CASCADE")
    elif enum_exists:
        # Enum существует, но таблицы нет - просто удаляем enum
        op.execute("DROP TYPE IF EXISTS adminactiontype CASCADE")

    # Создаем таблицу, если её нет
    if not table_exists:
        op.execute(
            """
            CREATE TABLE admin_action_logs (
                id SERIAL PRIMARY KEY,
                admin_id INTEGER NOT NULL,
                action_type VARCHAR(50) NOT NULL,
                details TEXT,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                CONSTRAINT fk_admin_action_logs_admin_id 
                    FOREIGN KEY (admin_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )

        # Создаем индексы
        op.create_index(
            "idx_admin_action_log_admin",
            "admin_action_logs",
            ["admin_id"],
            unique=False,
        )
        op.create_index(
            "idx_admin_action_log_admin_created",
            "admin_action_logs",
            ["admin_id", "created_at"],
            unique=False,
        )
        op.create_index(
            "idx_admin_action_log_created",
            "admin_action_logs",
            ["created_at"],
            unique=False,
        )
        op.create_index(
            "idx_admin_action_log_type",
            "admin_action_logs",
            ["action_type"],
            unique=False,
        )
    else:
        # Таблица существует, проверяем тип колонки action_type
        column_type = conn.execute(
            sa.text(
                "SELECT data_type FROM information_schema.columns "
                "WHERE table_name = 'admin_action_logs' AND column_name = 'action_type'"
            )
        ).scalar()
        
        # Если колонка имеет тип enum, изменяем на VARCHAR
        if column_type == 'USER-DEFINED':
            # Проверяем, является ли это enum
            is_enum = conn.execute(
                sa.text(
                    "SELECT EXISTS (SELECT 1 FROM pg_type t "
                    "JOIN pg_enum e ON t.oid = e.enumtypid "
                    "JOIN information_schema.columns c ON c.udt_name = t.typname "
                    "WHERE c.table_name = 'admin_action_logs' AND c.column_name = 'action_type')"
                )
            ).scalar()
            
            if is_enum:
                # Изменяем тип колонки на VARCHAR
                op.execute("ALTER TABLE admin_action_logs ALTER COLUMN action_type TYPE VARCHAR(50) USING action_type::text")
        
        # Проверяем и добавляем поле details, если его нет
        details_exists = conn.execute(
            sa.text(
                "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
                "WHERE table_name = 'admin_action_logs' AND column_name = 'details')"
            )
        ).scalar()

        if not details_exists:
            op.add_column(
                "admin_action_logs", sa.Column("details", sa.Text(), nullable=True)
            )


def downgrade() -> None:
    """Downgrade schema."""
    # Удаляем индексы
    try:
        op.drop_index("idx_admin_action_log_type", table_name="admin_action_logs")
    except Exception:
        pass
    try:
        op.drop_index("idx_admin_action_log_created", table_name="admin_action_logs")
    except Exception:
        pass
    try:
        op.drop_index("idx_admin_action_log_admin_created", table_name="admin_action_logs")
    except Exception:
        pass
    try:
        op.drop_index("idx_admin_action_log_admin", table_name="admin_action_logs")
    except Exception:
        pass
    # Удаляем таблицу
    try:
        op.drop_table("admin_action_logs")
    except Exception:
        pass
    # Удаляем enum (если существует)
    op.execute("DROP TYPE IF EXISTS adminactiontype CASCADE")
