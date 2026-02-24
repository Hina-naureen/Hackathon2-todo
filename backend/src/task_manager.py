# src/task_manager.py — Service layer
# References: specs/features/task-crud.md §Functional Requirements (FR-001–FR-013)
#             specs/architecture.md §Layer 2 — Service Layer
#             specs/constitution.md §III Architecture Rules

from src.models import Task, TaskStore


class TaskManager:
    """Business logic for all task CRUD operations.

    Contains no I/O. Accepts a TaskStore via constructor injection so the
    store can be replaced (e.g. a database session in Phase II) without
    modifying this class.

    Return-value signalling convention (architecture §Error Handling):
      - get_task / update_task / toggle_complete  → Task | None
      - delete_task                               → tuple[bool, str]
    No exceptions are raised for expected business conditions.
    """

    def __init__(self, store: TaskStore) -> None:
        self._store = store

    # ------------------------------------------------------------------
    # US-01  Create task
    # ------------------------------------------------------------------

    def add_task(self, title: str, description: str = "") -> Task:
        """Strip whitespace and delegate creation to TaskStore.

        Length validation is performed in the CLI layer because that is
        where user input originates. This method trusts its caller.
        """
        return self._store.add(title.strip(), description.strip())

    # ------------------------------------------------------------------
    # US-02  View tasks
    # ------------------------------------------------------------------

    def get_all_tasks(self) -> list[Task]:
        """Return all tasks ordered by ascending ID."""
        return self._store.get_all()

    def get_task(self, task_id: int) -> Task | None:
        """Return a single task by ID, or None if not found."""
        return self._store.get_by_id(task_id)

    # ------------------------------------------------------------------
    # US-03  Update task
    # ------------------------------------------------------------------

    def update_task(
        self,
        task_id: int,
        title: str | None = None,
        description: str | None = None,
    ) -> Task | None:
        """Update title and/or description of an existing task.

        A None argument means 'keep the existing value' (Enter-to-keep
        behaviour from the CLI).
        Returns the mutated Task, or None if task_id was not found.
        """
        task = self._store.get_by_id(task_id)
        if task is None:
            return None
        if title is not None and title.strip():
            task.title = title.strip()
        if description is not None:
            task.description = description.strip()
        return task

    # ------------------------------------------------------------------
    # US-04  Delete task
    # ------------------------------------------------------------------

    def delete_task(self, task_id: int) -> tuple[bool, str]:
        """Delete a task by ID after capturing its title.

        Returns:
            (True, task_title)  — task was found and removed.
            (False, "")         — task_id was not found; nothing changed.
        """
        task = self._store.get_by_id(task_id)
        if task is None:
            return False, ""
        title = task.title
        self._store.delete(task_id)
        return True, title

    # ------------------------------------------------------------------
    # US-05  Toggle completion
    # ------------------------------------------------------------------

    def toggle_complete(self, task_id: int) -> Task | None:
        """Flip the completed flag on a task.

        Returns the updated Task (with new completed value),
        or None if task_id was not found.
        """
        task = self._store.get_by_id(task_id)
        if task is None:
            return None
        task.completed = not task.completed
        return task
