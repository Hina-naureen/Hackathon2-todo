"""Initial schema — task table

Revision ID: 001
Revises:
Create Date: 2026-02-28

Creates the authoritative `task` table that backs all Phase II task CRUD.
Column definitions are the source of truth for Neon DB; SQLite dev uses the
same migration via Alembic or falls back to SQLModel create_all() on startup.

References: specs/database/schema.md
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "task",
        # Primary key — auto-incrementing integer, dialect-agnostic.
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),

        # Task content.
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=False, server_default=""),

        # Status flag — defaults to false (pending).
        sa.Column("completed", sa.Boolean(), nullable=False, server_default=sa.false()),

        # Owner — always populated from the validated JWT sub claim.
        # Not a FK in Phase II (YAGNI); enforced at the application layer.
        sa.Column("user_id", sa.String(), nullable=False),

        # Audit timestamps — stored as naive UTC datetimes.
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),

        sa.PrimaryKeyConstraint("id"),
    )

    # Index on user_id — every query filters by this column.
    op.create_index("ix_task_user_id", "task", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_task_user_id", table_name="task")
    op.drop_table("task")
