# src/database.py — Phase II database layer
# References: specs/database/schema.md
#             specs/phase2-migration-plan.md §TaskStore DB Adapter

from __future__ import annotations

import os
from collections.abc import Generator
from datetime import datetime, timezone

from sqlalchemy.pool import NullPool, QueuePool
from dotenv import load_dotenv
from sqlmodel import Session, SQLModel, create_engine, select

from src.db_models import Task

load_dotenv()

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

# Default to SQLite for local dev — set DATABASE_URL in .env for Neon DB.
# Accepted formats:
#   sqlite:///./dev.db
#   postgresql://...        (SQLAlchemy defaults to psycopg2 driver)
#   postgresql+psycopg2://...
DATABASE_URL: str = os.environ.get("DATABASE_URL", "sqlite:///./dev.db")

_is_sqlite = DATABASE_URL.startswith("sqlite")

# Detect Neon pooler endpoint ("-pooler" in the hostname).
# When using Neon's built-in PgBouncer, SQLAlchemy must NOT add its own
# connection pool on top — doing so causes double-pooling and exhausts Neon's
# connection limit. NullPool ensures each session checkout goes directly to
# PgBouncer, which manages the underlying Postgres connections.
_is_neon_pooler = not _is_sqlite and "-pooler" in DATABASE_URL

# SQLite needs check_same_thread=False; PostgreSQL needs no extra connect_args.
_connect_args: dict = {"check_same_thread": False} if _is_sqlite else {}

# Pool strategy:
#   SQLite         → no pool kwargs (SQLAlchemy uses StaticPool internally)
#   Neon pooler    → NullPool (PgBouncer already pools; double-pooling is harmful)
#   Neon direct    → QueuePool with pool_pre_ping and pool_recycle
_pool_kwargs: dict
if _is_sqlite:
    _pool_kwargs = {}
elif _is_neon_pooler:
    # NullPool: connections are opened and closed on every session checkout.
    # Safe and correct behind PgBouncer in transaction-pooling mode.
    _pool_kwargs = {"poolclass": NullPool}
else:
    # Direct Neon connection (not via pooler):
    #   pool_pre_ping  — re-validates connection on checkout; critical when
    #                    Neon scales to zero and drops idle connections.
    #   pool_recycle   — discard connections older than 5 min.
    #   pool_size      — base number of persistent connections.
    #   max_overflow   — burst headroom above pool_size.
    _pool_kwargs = {
        "poolclass": QueuePool,
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_size": 5,
        "max_overflow": 10,
    }

engine = create_engine(DATABASE_URL, connect_args=_connect_args, echo=False, **_pool_kwargs)


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
