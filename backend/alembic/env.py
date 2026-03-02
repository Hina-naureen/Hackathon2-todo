# alembic/env.py — Alembic migration environment
# References: specs/database/schema.md
#
# Key responsibilities:
#   1. Load DATABASE_URL from backend/.env (same source as the FastAPI app).
#   2. Import all SQLModel table models so Alembic sees the full metadata.
#   3. Run migrations in "offline" mode (emit SQL) or "online" mode (live DB).

from __future__ import annotations

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

# ---------------------------------------------------------------------------
# Ensure 'backend/' is on sys.path so `from src.db_models import Task` works
# when alembic is invoked from the backend/ directory.
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# ---------------------------------------------------------------------------
# Import all table models — REQUIRED so Alembic registers them in metadata.
# Adding a new table model: import it here and Alembic will detect it.
# ---------------------------------------------------------------------------
from src.db_models import Task  # noqa: F401, E402

# ---------------------------------------------------------------------------
# Load .env so DATABASE_URL is available without the user having to export it.
# ---------------------------------------------------------------------------
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

# ---------------------------------------------------------------------------
# Alembic Config object — gives access to values in alembic.ini.
# ---------------------------------------------------------------------------
config = context.config

# Inject DATABASE_URL into Alembic's config at runtime.
# This overrides the blank sqlalchemy.url in alembic.ini.
_database_url = os.environ.get("DATABASE_URL", "sqlite:///./dev.db")
config.set_main_option("sqlalchemy.url", _database_url)

# ---------------------------------------------------------------------------
# Logging — honour the [loggers] section in alembic.ini.
# ---------------------------------------------------------------------------
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---------------------------------------------------------------------------
# target_metadata — the SQLModel metadata that Alembic diffs against.
# ---------------------------------------------------------------------------
target_metadata = SQLModel.metadata


# ---------------------------------------------------------------------------
# Offline mode — emit SQL to stdout without a live database connection.
# Usage: uv run alembic upgrade head --sql
# ---------------------------------------------------------------------------
def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online mode — connect to the live database and apply migrations directly.
# Usage: uv run alembic upgrade head
# ---------------------------------------------------------------------------
def run_migrations_online() -> None:
    _is_sqlite = _database_url.startswith("sqlite")

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.StaticPool if _is_sqlite else pool.NullPool,
        connect_args={"check_same_thread": False} if _is_sqlite else {},
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,       # detect column type changes
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
