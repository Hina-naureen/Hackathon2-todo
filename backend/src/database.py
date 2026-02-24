# src/database.py — Phase II database layer
# References: specs/database/schema.md
#             specs/phase2-migration-plan.md §TaskStore DB Adapter

from __future__ import annotations

import os
from collections.abc import Generator
from datetime import datetime, timezone

from dotenv import load_dotenv
from sqlmodel import Session, SQLModel, create_engine, select

from src.db_models import Task

load_dotenv()

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

# Default to SQLite for local dev — set DATABASE_URL in .env for Neon DB.
DATABASE_URL: str = os.environ.get("DATABASE_URL", "sqlite:///./dev.db")

_connect_args: dict = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=_connect_args, echo=False)


def create_db_and_tables() -> None:
    """Create all SQLModel tables if they do not already exist."""
    SQLModel.metadata.create_all(engine)


# ---------------------------------------------------------------------------
# Session dependency (FastAPI Depends)
# ---------------------------------------------------------------------------


def get_session() -> Generator[Session, None, None]:
    """Yield a SQLModel session; close on exit."""
    with Session(engine) as session:
        yield session


# ---------------------------------------------------------------------------
# DB-backed TaskStore adapter
# ---------------------------------------------------------------------------


class DBTaskStore:
    """Same public interface as Phase I's in-memory TaskStore.

    Wraps a SQLModel Session scoped to the current request and a user_id
    extracted from the validated JWT. TaskManager (Phase I, unchanged) is
    passed this adapter via constructor injection and works without
    modification because it only calls add / get_all / get_by_id / delete.
    """

    def __init__(self, session: Session, user_id: str) -> None:
        self._session = session
        self._user_id = user_id

    def add(self, title: str, description: str = "") -> Task:
        """Insert a new task row and return it with the auto-assigned id."""
        task = Task(title=title, description=description, user_id=self._user_id)
        self._session.add(task)
        self._session.flush()      # assigns id within the current transaction
        self._session.refresh(task)
        return task

    def get_all(self) -> list[Task]:
        """Return all tasks for this user ordered by ascending id."""
        return list(
            self._session.exec(
                select(Task)
                .where(Task.user_id == self._user_id)
                .order_by(Task.id)
            ).all()
        )

    def get_by_id(self, task_id: int) -> Task | None:
        """Return the task with the given id scoped to this user, or None."""
        return self._session.exec(
            select(Task).where(Task.id == task_id, Task.user_id == self._user_id)
        ).first()

    def delete(self, task_id: int) -> bool:
        """Delete the task. Returns True on success, False if not found."""
        task = self.get_by_id(task_id)
        if task is None:
            return False
        self._session.delete(task)
        return True


def _utcnow() -> datetime:
    """Naive UTC datetime helper for route handlers."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
