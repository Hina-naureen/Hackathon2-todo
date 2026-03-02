# src/routes/tasks.py — Task CRUD + toggle route handlers
# References: specs/api/rest-endpoints.md
#             specs/database/schema.md §TaskStore DB Adapter

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from src.auth.dependencies import get_current_user
from src.database import DBTaskStore, _utcnow, get_session
from src.db_models import Task, TaskCreate, TaskRead, TaskUpdate
from src.models import MAX_DESCRIPTION_LENGTH, MAX_TITLE_LENGTH
from src.task_manager import TaskManager

router = APIRouter()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _manager(session: Session, user_id: str) -> TaskManager:
    """Wire Phase I TaskManager with the Phase II DB-backed store."""
    return TaskManager(DBTaskStore(session, user_id))  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# GET /api/tasks
# ---------------------------------------------------------------------------


@router.get("", response_model=list[TaskRead])
async def list_tasks(
    user_id: str = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> list[Task]:
    """Return all tasks for the authenticated user, ordered by ascending id."""
    return _manager(session, user_id).get_all_tasks()  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# POST /api/tasks
# ---------------------------------------------------------------------------


@router.post("", response_model=TaskRead, status_code=201)
async def create_task(
    body: TaskCreate,
    user_id: str = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Task:
    """Create a new task. Returns the created task with its auto-assigned id."""
    title = body.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="Title cannot be empty.")
    if len(title) > MAX_TITLE_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Title must be {MAX_TITLE_LENGTH} characters or fewer.",
        )
    if len(body.description) > MAX_DESCRIPTION_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Description must be {MAX_DESCRIPTION_LENGTH} characters or fewer.",
        )

    task = _manager(session, user_id).add_task(title, body.description)
    if body.due_date is not None:
        task.due_date = body.due_date  # type: ignore[assignment]
    session.commit()
    session.refresh(task)
    return task  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# GET /api/tasks/{task_id}
# ---------------------------------------------------------------------------


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(
    task_id: int,
    user_id: str = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Task:
    """Return a single task by id. 404 if not found or owned by another user."""
    task = _manager(session, user_id).get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task #{task_id} not found.")
    return task  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# PUT /api/tasks/{task_id}
# ---------------------------------------------------------------------------


@router.put("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: int,
    body: TaskUpdate,
    user_id: str = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Task:
    """Update title and/or description. null fields keep the existing value."""
    # Validate non-null title before touching the DB.
    if body.title is not None:
        stripped = body.title.strip()
        if not stripped:
            raise HTTPException(status_code=400, detail="Title cannot be empty.")
        if len(stripped) > MAX_TITLE_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"Title must be {MAX_TITLE_LENGTH} characters or fewer.",
            )
        # Pass the already-stripped title so TaskManager doesn't double-strip.
        title_arg: str | None = stripped
    else:
        title_arg = None

    if body.description is not None and len(body.description) > MAX_DESCRIPTION_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Description must be {MAX_DESCRIPTION_LENGTH} characters or fewer.",
        )

    task = _manager(session, user_id).update_task(task_id, title_arg, body.description)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task #{task_id} not found.")

    if body.due_date is not None:
        task.due_date = body.due_date  # type: ignore[assignment]
    task.updated_at = _utcnow()  # type: ignore[assignment]
    session.commit()
    session.refresh(task)
    return task  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# DELETE /api/tasks/{task_id}
# ---------------------------------------------------------------------------


@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    user_id: str = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> dict[str, str]:
    """Permanently delete a task. Returns a confirmation message."""
    success, _ = _manager(session, user_id).delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Task #{task_id} not found.")
    session.commit()
    return {"detail": f"Task #{task_id} deleted."}


# ---------------------------------------------------------------------------
# PATCH /api/tasks/{task_id}/toggle
# ---------------------------------------------------------------------------


@router.patch("/{task_id}/toggle", response_model=TaskRead)
async def toggle_task(
    task_id: int,
    user_id: str = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Task:
    """Toggle the completed status of a task between true and false."""
    task = _manager(session, user_id).toggle_complete(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task #{task_id} not found.")

    task.updated_at = _utcnow()  # type: ignore[assignment]
    session.commit()
    session.refresh(task)
    return task  # type: ignore[return-value]
