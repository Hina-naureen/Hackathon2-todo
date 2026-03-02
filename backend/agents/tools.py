# agents/tools.py — MCP-style tool functions for TaskAgent
# References: specs/api/mcp-tools.md
#             specs/agents/agent-behavior.md §Tool Dispatch
#             specs/features/chatbot.md §FR-CHAT-011 (due_date)

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlmodel import Session

from src.database import DBTaskStore, _utcnow
from src.models import MAX_DESCRIPTION_LENGTH, MAX_TITLE_LENGTH
from src.task_manager import TaskManager


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _manager(session: Session, user_id: str) -> TaskManager:
    """Wire Phase I TaskManager with the DB-backed store, scoped to user_id."""
    return TaskManager(DBTaskStore(session, user_id))  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Tool functions
# Each function returns a plain dict.
# Errors are returned as {"error": "..."} — never raised as exceptions —
# so the agent can relay them naturally in the reply.
# References: specs/api/mcp-tools.md §Tool Definitions
# ---------------------------------------------------------------------------


def _parse_due_date(due_date: str | None) -> datetime | None:
    """Parse an ISO 8601 string from the LLM into a naive UTC datetime.

    Returns None for None or empty string. Raises ValueError on bad format
    so the caller can return a clean {"error": ...} dict.
    """
    if not due_date:
        return None
    # fromisoformat handles "2026-03-03T14:00:00" and "2026-03-03"
    dt = datetime.fromisoformat(due_date)
    # Strip timezone info — stored as naive UTC (matches created_at/updated_at)
    return dt.replace(tzinfo=None)


def create_task(
    session: Session,
    user_id: str,
    title: str,
    description: str = "",
    due_date: str | None = None,
) -> dict[str, Any]:
    """Create a task. Returns the created task dict or {"error": "..."}.

    References: specs/api/mcp-tools.md §create_task
    """
    title = title.strip()
    if not title:
        return {"error": "Title cannot be empty."}
    if len(title) > MAX_TITLE_LENGTH:
        return {"error": f"Title must be {MAX_TITLE_LENGTH} characters or fewer."}
    if len(description) > MAX_DESCRIPTION_LENGTH:
        return {"error": f"Description must be {MAX_DESCRIPTION_LENGTH} characters or fewer."}

    try:
        parsed_due = _parse_due_date(due_date)
    except ValueError:
        return {"error": f"Invalid due_date format '{due_date}'. Use ISO 8601 (e.g. '2026-03-03T14:00:00')."}

    task = _manager(session, user_id).add_task(title, description)
    if parsed_due is not None:
        task.due_date = parsed_due  # type: ignore[assignment]
    session.commit()
    session.refresh(task)
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "completed": task.completed,
        "due_date": task.due_date.isoformat() if task.due_date else None,
    }


def list_tasks(
    session: Session,
    user_id: str,
    filter: str = "all",
) -> dict[str, Any]:
    """Return the user's tasks, optionally filtered by completion status."""
    tasks = _manager(session, user_id).get_all_tasks()

    if filter == "pending":
        tasks = [t for t in tasks if not t.completed]
    elif filter == "completed":
        tasks = [t for t in tasks if t.completed]

    return {
        "tasks": [
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "completed": t.completed,
                "due_date": t.due_date.isoformat() if t.due_date else None,  # type: ignore[union-attr]
            }
            for t in tasks
        ],
        "count": len(tasks),
    }


def update_task(
    session: Session,
    user_id: str,
    id: int,
    title: str | None = None,
    description: str | None = None,
    due_date: str | None = None,
) -> dict[str, Any]:
    """Update a task's title, description, and/or due_date. Returns updated task or error.

    References: specs/api/mcp-tools.md §update_task
    """
    if title is not None:
        title = title.strip()
        if not title:
            return {"error": "Title cannot be empty."}
        if len(title) > MAX_TITLE_LENGTH:
            return {"error": f"Title must be {MAX_TITLE_LENGTH} characters or fewer."}

    if description is not None and len(description) > MAX_DESCRIPTION_LENGTH:
        return {"error": f"Description must be {MAX_DESCRIPTION_LENGTH} characters or fewer."}

    try:
        parsed_due = _parse_due_date(due_date)
    except ValueError:
        return {"error": f"Invalid due_date format '{due_date}'. Use ISO 8601 (e.g. '2026-03-03T14:00:00')."}

    task = _manager(session, user_id).update_task(id, title, description)
    if task is None:
        return {"error": f"Task #{id} not found."}

    if due_date is not None:
        # Empty string clears the due date; non-empty sets it
        task.due_date = parsed_due  # type: ignore[assignment]
    task.updated_at = _utcnow()  # type: ignore[assignment]
    session.commit()
    session.refresh(task)
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "completed": task.completed,
        "due_date": task.due_date.isoformat() if task.due_date else None,
    }


def delete_task(
    session: Session,
    user_id: str,
    id: int,
) -> dict[str, Any]:
    """Delete a task by ID. Returns confirmation or error."""
    deleted, title = _manager(session, user_id).delete_task(id)
    if not deleted:
        return {"error": f"Task #{id} not found."}
    session.commit()
    return {"deleted": True, "id": id, "title": title}


def toggle_complete(
    session: Session,
    user_id: str,
    id: int,
) -> dict[str, Any]:
    """Toggle a task's completed flag. Returns updated task or error."""
    task = _manager(session, user_id).toggle_complete(id)
    if task is None:
        return {"error": f"Task #{id} not found."}

    task.updated_at = _utcnow()  # type: ignore[assignment]
    session.commit()
    session.refresh(task)
    return {
        "id": task.id,
        "title": task.title,
        "completed": task.completed,
    }


# ---------------------------------------------------------------------------
# Tool registry + dispatch
# References: specs/api/mcp-tools.md §Tool Dispatch
# ---------------------------------------------------------------------------

TOOL_REGISTRY: dict[str, Any] = {
    "create_task": create_task,
    "list_tasks": list_tasks,
    "update_task": update_task,
    "delete_task": delete_task,
    "toggle_complete": toggle_complete,
}


def call_tool(
    session: Session,
    user_id: str,
    tool_name: str,
    args: dict[str, Any],
) -> Any:
    """Dispatch a tool call by name.

    Returns the tool result dict, or {"error": "Unknown tool: <name>"} for
    unrecognised names. user_id is always injected — it is never read from args.
    """
    fn = TOOL_REGISTRY.get(tool_name)
    if fn is None:
        return {"error": f"Unknown tool: {tool_name}"}
    return fn(session, user_id, **args)


# ---------------------------------------------------------------------------
# OpenAI function-calling schemas
# References: specs/api/mcp-tools.md §OpenAI Tool Schema
# ---------------------------------------------------------------------------

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "create_task",
            "description": "Create a new task for the authenticated user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Task title (max 200 characters, non-empty).",
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional task description (max 500 characters).",
                    },
                    "due_date": {
                        "type": "string",
                        "description": (
                            "Optional due date in ISO 8601 format (e.g. '2026-03-03T14:00:00'). "
                            "Convert any natural-language date/time in the user's message "
                            "(e.g. 'tomorrow at 2 PM', 'Friday') to ISO 8601 before calling. "
                            "Omit if no date was mentioned."
                        ),
                    },
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_tasks",
            "description": (
                "List tasks for the authenticated user, optionally filtered by status."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "filter": {
                        "type": "string",
                        "enum": ["all", "pending", "completed"],
                        "description": "Filter by completion status. Defaults to 'all'.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_task",
            "description": (
                "Update the title, description, and/or due_date of an existing task. "
                "Omit any field to keep its current value."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer",
                        "description": "The task ID to update.",
                    },
                    "title": {
                        "type": "string",
                        "description": "New title (omit to keep existing).",
                    },
                    "description": {
                        "type": "string",
                        "description": "New description (omit to keep existing).",
                    },
                    "due_date": {
                        "type": "string",
                        "description": (
                            "New due date in ISO 8601 format (e.g. '2026-03-06T10:00:00'). "
                            "Pass empty string '' to clear the due date. "
                            "Omit to keep existing due date."
                        ),
                    },
                },
                "required": ["id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_task",
            "description": "Permanently delete a task by ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer",
                        "description": "The task ID to delete.",
                    },
                },
                "required": ["id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "toggle_complete",
            "description": (
                "Toggle a task's completed status between true (done) and false (pending)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer",
                        "description": "The task ID to toggle.",
                    },
                },
                "required": ["id"],
            },
        },
    },
]
