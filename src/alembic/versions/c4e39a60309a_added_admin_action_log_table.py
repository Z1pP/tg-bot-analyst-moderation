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

    # Проверяем, существует ли enum
    enum_exists = conn.execute(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'adminactiontype')"
        )
    ).scalar()

    # Если enum существует, проверяем его значения
    if enum_exists:
        # Проверяем, есть ли неправильные значения (в верхнем регистре)
        enum_values = conn.execute(
            sa.text(
                "SELECT enumlabel FROM pg_enum "
                "WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'adminactiontype') "
                "ORDER BY enumsortorder"
            )
        ).fetchall()
        
        # Проверяем, есть ли значения в верхнем регистре
        has_uppercase = any(
            value[0] in [
                "REPORT_USER",
                "REPORT_CHAT",
                "REPORT_ALL_USERS",
                "ADD_TEMPLATE",
                "DELETE_TEMPLATE",
                "ADD_CATEGORY",
                "DELETE_CATEGORY",
                "SEND_MESSAGE",
                "DELETE_MESSAGE",
                "REPLY_MESSAGE",
            ]
            for value in enum_values
        )

        if has_uppercase:
            # Если таблица существует, нужно удалить её сначала
            if table_exists:
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
                op.drop_table("admin_action_logs")
            
            # Удаляем старый enum
            op.execute("DROP TYPE IF EXISTS adminactiontype CASCADE")
            enum_exists = False
            table_exists = False

    # Создаем enum с правильными значениями (в нижнем регистре)
    if not enum_exists:
        op.execute(
            "CREATE TYPE adminactiontype AS ENUM "
            "('report_user', 'report_chat', 'report_all_users', 'add_template', "
            "'delete_template', 'add_category', 'delete_category', 'send_message', "
            "'delete_message', 'reply_message')"
        )

    # Создаем таблицу, если её нет
    if not table_exists:
        op.execute(
            """
            CREATE TABLE admin_action_logs (
                id SERIAL PRIMARY KEY,
                admin_id INTEGER NOT NULL,
                action_type adminactiontype NOT NULL,
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
        # Таблица существует, проверяем и добавляем поле details, если его нет
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
    # Удаляем enum
    op.execute("DROP TYPE IF EXISTS adminactiontype CASCADE")
