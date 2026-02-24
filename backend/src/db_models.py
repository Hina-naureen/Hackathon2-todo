# src/db_models.py — Phase II SQLModel schemas
# References: specs/database/schema.md
#             specs/api/rest-endpoints.md §Shared Schemas

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    """Naive UTC datetime (timezone-aware replacement for deprecated utcnow)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ---------------------------------------------------------------------------
# Table model
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


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class TaskCreate(SQLModel):
    """Input schema for POST /api/tasks."""

    title: str
    description: str = ""


class TaskUpdate(SQLModel):
    """Input schema for PUT /api/tasks/{id}.

    null (None) means 'keep the existing value'.
    An empty string for title is a validation error (caught in the route handler).
    An empty string for description clears the description.
    """

    title: Optional[str] = None
    description: Optional[str] = None


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
