# src/models.py — Data layer
# References: specs/features/task-crud.md §Key Entities
#             specs/constitution.md §IV Naming Conventions
#             specs/architecture.md §Layer 1 — Data Layer

from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Constants (constitution §II — magic numbers FORBIDDEN)
# ---------------------------------------------------------------------------

MAX_TITLE_LENGTH: int = 200
MAX_DESCRIPTION_LENGTH: int = 500
DISPLAY_DESCRIPTION_LIMIT: int = 30
STATUS_COMPLETE: str = "[x]"
STATUS_PENDING: str  = "[ ]"


# ---------------------------------------------------------------------------
# Domain object
# ---------------------------------------------------------------------------


@dataclass
class Task:
    """Single to-do item. Mutable; mutation is performed by TaskManager only."""

    id: int
    title: str
    description: str = ""
    completed: bool = False


# ---------------------------------------------------------------------------
# In-memory store
# ---------------------------------------------------------------------------


class TaskStore:
    """In-memory collection of Task objects. Owns the ID counter.

    Backing structure is dict[int, Task] for O(1) lookup by ID.
    The public interface is intentionally thin so Phase II can swap this
    class for a database session without changing any other module.
    """

    def __init__(self) -> None:
        self._tasks: dict[int, Task] = {}
        self._next_id: int = 1

    def add(self, title: str, description: str = "") -> Task:
        """Create a new Task, assign the next ID, persist, and return it."""
        task = Task(id=self._next_id, title=title, description=description)
        self._tasks[self._next_id] = task
        self._next_id += 1
        return task

    def get_all(self) -> list[Task]:
        """Return all tasks sorted by ascending ID."""
        return sorted(self._tasks.values(), key=lambda t: t.id)

    def get_by_id(self, task_id: int) -> Task | None:
        """Return the Task with the given ID, or None if absent."""
        return self._tasks.get(task_id)

    def delete(self, task_id: int) -> bool:
        """Remove the Task with the given ID.

        Returns True on success, False if task_id was not found.
        """
        if task_id not in self._tasks:
            return False
        del self._tasks[task_id]
        return True
