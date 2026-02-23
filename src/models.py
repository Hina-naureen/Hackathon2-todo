# [Task]: T-001
# [From]: specs/phase1-console/spec.md §Data Model, specs/phase1-console/plan.md §Data Layer

from dataclasses import dataclass, field


@dataclass
class Task:
    id: int
    title: str
    description: str = ""
    completed: bool = False


class TaskStore:
    def __init__(self) -> None:
        self._tasks: list[Task] = []
        self._next_id: int = 1

    def add(self, title: str, description: str = "") -> Task:
        task = Task(id=self._next_id, title=title, description=description)
        self._tasks.append(task)
        self._next_id += 1
        return task

    def get_all(self) -> list[Task]:
        return list(self._tasks)

    def get_by_id(self, task_id: int) -> Task | None:
        for task in self._tasks:
            if task.id == task_id:
                return task
        return None

    def delete(self, task_id: int) -> bool:
        task = self.get_by_id(task_id)
        if task is None:
            return False
        self._tasks.remove(task)
        return True
