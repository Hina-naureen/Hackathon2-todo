# [Task]: T-003
# [From]: specs/phase1-console/spec.md §Application Flow, specs/phase1-console/plan.md §UI Layer

from src.models import Task
from src.task_service import TaskService


def print_menu() -> None:
    print("\n" + "=" * 40)
    print("         TODO APP - Phase I")
    print("=" * 40)
    print("  1. Add Task")
    print("  2. View All Tasks")
    print("  3. Update Task")
    print("  4. Delete Task")
    print("  5. Toggle Complete/Incomplete")
    print("  0. Exit")
    print("=" * 40)


def print_tasks(tasks: list[Task]) -> None:
    if not tasks:
        print("\nNo tasks found.")
        return

    print(f"\n{'ID':<5} {'Status':<12} {'Title':<25} {'Description'}")
    print("-" * 70)
    for task in tasks:
        status = "[DONE]" if task.completed else "[    ]"
        title = task.title[:23] + ".." if len(task.title) > 25 else task.title
        desc = task.description[:28] + ".." if len(task.description) > 30 else task.description
        print(f"{task.id:<5} {status:<12} {title:<25} {desc}")
    print(f"\nTotal: {len(tasks)} task(s)")


def handle_add(service: TaskService) -> None:
    print("\n--- Add New Task ---")
    title = input("Title (required): ").strip()
    if not title:
        print("Error: Title cannot be empty.")
        return
    if len(title) > 200:
        print("Error: Title must be 200 characters or less.")
        return

    description = input("Description (optional): ").strip()
    if len(description) > 500:
        print("Error: Description must be 500 characters or less.")
        return

    task = service.add_task(title, description)
    print(f"Task #{task.id} added successfully.")


def handle_view(service: TaskService) -> None:
    print("\n--- All Tasks ---")
    tasks = service.get_all_tasks()
    print_tasks(tasks)


def handle_update(service: TaskService) -> None:
    print("\n--- Update Task ---")
    raw_id = input("Enter Task ID to update: ").strip()
    if not raw_id.isdigit():
        print("Error: Please enter a valid task ID.")
        return

    task_id = int(raw_id)
    task = service.get_all_tasks()
    existing = next((t for t in task if t.id == task_id), None)
    if existing is None:
        print(f"Error: Task #{task_id} not found.")
        return

    print(f"Current title: {existing.title}")
    new_title = input("New title (press Enter to keep current): ").strip()

    print(f"Current description: {existing.description or '(none)'}")
    new_description = input("New description (press Enter to keep current): ")

    title_arg = new_title if new_title else None
    desc_arg = new_description.strip() if new_description.strip() != "" else None

    updated = service.update_task(
        task_id,
        title=title_arg,
        description=desc_arg,
    )
    if updated:
        print(f"Task #{task_id} updated successfully.")


def handle_delete(service: TaskService) -> None:
    print("\n--- Delete Task ---")
    raw_id = input("Enter Task ID to delete: ").strip()
    if not raw_id.isdigit():
        print("Error: Please enter a valid task ID.")
        return

    task_id = int(raw_id)
    tasks = service.get_all_tasks()
    existing = next((t for t in tasks if t.id == task_id), None)
    if existing is None:
        print(f"Error: Task #{task_id} not found.")
        return

    confirm = input(f"Delete task '{existing.title}'? (y/n): ").strip().lower()
    if confirm == "y":
        service.delete_task(task_id)
        print(f"Task #{task_id} deleted.")
    else:
        print("Delete cancelled.")


def handle_toggle(service: TaskService) -> None:
    print("\n--- Toggle Task Status ---")
    raw_id = input("Enter Task ID to toggle: ").strip()
    if not raw_id.isdigit():
        print("Error: Please enter a valid task ID.")
        return

    task_id = int(raw_id)
    task = service.toggle_complete(task_id)
    if task is None:
        print(f"Error: Task #{task_id} not found.")
        return

    status = "complete" if task.completed else "pending"
    print(f"Task #{task_id} marked as {status}.")
