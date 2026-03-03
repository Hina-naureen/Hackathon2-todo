# src/app.py — FastAPI application entry point (Phase II)
# References: specs/overview.md §Repository Structure
#             specs/api/rest-endpoints.md §CORS Configuration
#
# Run:  uv run uvicorn src.app:app --reload   (from backend/)
# Docs: http://localhost:8000/docs

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sqlmodel import Session, text

from src.database import create_db_and_tables, engine, get_session
from src.routes.chat import router as chat_router
from src.routes.tasks import router as tasks_router


# ---------------------------------------------------------------------------
# Lifespan — create tables once on startup
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    create_db_and_tables()
    yield


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Todo API — Phase II",
    version="2.0.0",
    description="Evolution of Todo — REST API backend (FastAPI + SQLModel + Neon DB)",
    lifespan=lifespan,
)

# CORS — allow the Next.js frontend in development.
# Set ALLOWED_ORIGINS in .env for production.
import os
from dotenv import load_dotenv
load_dotenv()

_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(tasks_router, prefix="/api/tasks", tags=["tasks"])
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/db", tags=["health"])
async def health_db() -> dict[str, str]:
    """Verify the database connection is reachable.

    Executes a minimal round-trip query (SELECT 1) and returns the database
    dialect so callers can confirm SQLite vs PostgreSQL without inspecting
    environment variables.
    """
    from fastapi import HTTPException  # noqa: PLC0415

    try:
        with Session(engine) as session:
            session.exec(text("SELECT 1"))
        dialect = engine.dialect.name          # "sqlite" or "postgresql"
        return {"status": "ok", "dialect": dialect}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database unreachable: {exc}") from exc
