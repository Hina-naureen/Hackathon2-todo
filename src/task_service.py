# [Task]: T-002
# [From]: specs/phase1-console/spec.md §User Stories, specs/phase1-console/plan.md §Service Layer

from src.models import Task, TaskStore


class TaskService:
    def __init__(self, store: TaskStore) -> None:
        self._store = store

    def add_task(self, title: str, description: str = "") -> Task:
        return self._store.add(title.strip(), description.strip())

    def get_all_tasks(self) -> list[Task]:
        return self._store.get_all()

    def update_task(
        self,
        task_id: int,
        title: str | None = None,
        description: str | None = None,
    ) -> Task | None:
        task = self._store.get_by_id(task_id)
        if task is None:
            return None
        if title is not None and title.strip():
            task.title = title.strip()
        if description is not None:
            task.description = description.strip()
        return task

    def delete_task(self, task_id: int) -> tuple[bool, str]:
        task = self._store.get_by_id(task_id)
        if task is None:
            return False, ""
        title = task.title
        self._store.delete(task_id)
        return True, title

    def toggle_complete(self, task_id: int) -> Task | None:
        task = self._store.get_by_id(task_id)
        if task is None:
            return None
        task.completed = not task.completed
        return task
