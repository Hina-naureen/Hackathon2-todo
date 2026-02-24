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

from src.database import create_db_and_tables
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

# CORS — allow the Next.js frontend on port 3000 in development.
# Set ALLOWED_ORIGINS in .env for production.
import os

_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

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
