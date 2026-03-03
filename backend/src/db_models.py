# src/db_models.py — Phase II + III SQLModel schemas
# References: specs/database/schema.md
#             specs/api/rest-endpoints.md §Shared Schemas
#             specs/api/mcp-tools.md §create_task, update_task (due_date)

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import uuid

from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    """Naive UTC datetime (timezone-aware replacement for deprecated utcnow)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ---------------------------------------------------------------------------
# User table
# ---------------------------------------------------------------------------


class AppUser(SQLModel, table=True):
    """Registered user — stores hashed password in Neon DB."""

    __tablename__ = "app_users"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
    )
    name: str = Field(max_length=100)
    email: str = Field(unique=True, index=True, max_length=200)
    password_hash: str


# ---------------------------------------------------------------------------
# Task table
# ---------------------------------------------------------------------------


class Task(SQLModel, table=True):
    """Persistent task row in Neon DB / SQLite.

    user_id is always set from the validated JWT sub claim — never from the
    request body. It scopes every query so users can only see their own tasks.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=200)
    description: str = Field(default="", max_length=500)
    completed: bool = Field(default=False)
    user_id: str = Field(index=True)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
    # Phase III — optional due date; NULL = no due date set.
    # Stored as naive UTC; agent converts natural-language dates to ISO 8601.
    due_date: Optional[datetime] = Field(default=None, nullable=True)


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class TaskCreate(SQLModel):
    """Input schema for POST /api/tasks."""

    title: str
    description: str = ""
    due_date: Optional[datetime] = None


class TaskUpdate(SQLModel):
    """Input schema for PUT /api/tasks/{id}.

    null (None) means 'keep the existing value'.
    An empty string for title is a validation error (caught in the route handler).
    An empty string for description clears the description.
    An empty string for due_date clears the due date.
    """

    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Response schema
# ---------------------------------------------------------------------------


class TaskRead(SQLModel):
    """Output schema for all task responses. user_id is never exposed."""

    id: int
    title: str
    description: str
    completed: bool
    created_at: datetime
    updated_at: datetime
    due_date: Optional[datetime] = None
