"""Add due_date column to task table — Phase III

Revision ID: 002
Revises: 001
Create Date: 2026-03-02

Adds an optional due_date (TIMESTAMP, nullable) column to the existing task
table so the AI agent can record due dates parsed from natural language input.

References: specs/api/mcp-tools.md §create_task, §update_task
            specs/features/chatbot.md §US-CHAT-08, §FR-CHAT-011
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # NULL-able: existing rows get NULL (no due date), which is correct.
    op.add_column(
        "task",
        sa.Column("due_date", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("task", "due_date")
