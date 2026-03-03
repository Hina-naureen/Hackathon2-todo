"""Add app_users table for custom auth

Revision ID: 003
Revises: 002
Create Date: 2026-03-03

Creates the app_users table that backs the custom sign-up / sign-in endpoints.
Passwords are stored as scrypt hashes — never plaintext.

References: specs/features/auth.md §AppUser
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "app_users",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=200), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_app_users_email", "app_users", ["email"])


def downgrade() -> None:
    op.drop_index("ix_app_users_email", table_name="app_users")
    op.drop_table("app_users")
