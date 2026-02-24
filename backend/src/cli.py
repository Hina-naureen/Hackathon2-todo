# src/cli.py — CLI layer
# References: specs/features/task-crud.md §Application Flow, §Error Catalogue
#             specs/architecture.md §Layer 3 — CLI Layer
#             specs/constitution.md §VII Error Handling Contract

from src.models import (
    Task,
    MAX_TITLE_LENGTH,
    MAX_DESCRIPTION_LENGTH,
    DISPLAY_DESCRIPTION_LIMIT,
    STATUS_COMPLETE,
    STATUS_PENDING,
)
from src.task_manager import TaskManager

# ---------------------------------------------------------------------------
# Layout constants  (constitution §II — magic numbers FORBIDDEN)
# ---------------------------------------------------------------------------

_APP_TITLE: str = "TODO APP  -  PHASE I"
_BOX_W: int = 44  # inner character width of the menu box

# Pre-built menu border strings  (avoids recomputing on every render)
_BOX_TOP: str = "  +" + "-" * _BOX_W + "+"
_BOX_MID: str = "  |" + " " * _BOX_W + "|"

# Task table column widths
_COL_ID: int     = 4
_COL_STATUS: int = 6
_COL_TITLE: int  = 26
_COL_DESC: int   = 22

# Total inner table width: sum of columns + 3 × two-space gaps
_TBL_W: int = _COL_ID + 2 + _COL_STATUS + 2 + _COL_TITLE + 2 + _COL_DESC  # = 64

# Pre-built table borders
_TBL_HEAVY: str = "  " + "=" * _TBL_W   # used for top/bottom of table
_TBL_LIGHT: str = "  " + "-" * _TBL_W   # used under the header row

# Section operation header underline
_SEC_LINE: str = "  " + "-" * _BOX_W

# Ordered menu entries — (key, label)
_MENU_ITEMS: tuple[tuple[str, str], ...] = (
    ("1", "Add Task"),
    ("2", "View All Tasks"),
    ("3", "Update Task"),
    ("4", "Delete Task"),
    ("5", "Toggle Complete / Incomplete"),
    ("0", "Exit"),
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _box_row(text: str) -> str:
    """Format one menu row: two leading indent spaces then text, padded to box width."""
    return f"  |  {text:<{_BOX_W - 2}}|"


def _section(title: str) -> None:
    """Print a labelled section header before each operation."""
    print(f"\n  >> {title}")
    print(_SEC_LINE)


def _truncate(text: str, limit: int) -> str:
    """Truncate text to limit chars, appending '..' when over the limit."""
    if len(text) <= limit:
        return text
    return text[: limit - 2] + ".."


def _prompt_task_id(label: str) -> int | None:
    """Prompt for a task ID; print an error and return None on invalid input.

    Rejects non-digit strings and values less than 1 (spec §Error Catalogue).
    """
    raw = input(f"  {label:<20} : ").strip()
    if not raw.isdigit() or int(raw) < 1:
        print("  Error: Please enter a valid task ID.")
        return None
    return int(raw)


# ---------------------------------------------------------------------------
# Menu & display
# ---------------------------------------------------------------------------


def print_menu() -> None:
    """Render the boxed numbered main menu to stdout."""
    print()
    print(_BOX_TOP)
    print(f"  |{_APP_TITLE.center(_BOX_W)}|")
    print(_BOX_TOP)
    print(_BOX_MID)
    for num, label in _MENU_ITEMS:
        print(_box_row(f"[{num}]  {label}"))
    print(_BOX_MID)
    print(_BOX_TOP)


def print_tasks(tasks: list[Task]) -> None:
    """Format and print all tasks as a bordered table.

    Prints 'No tasks found.' when the list is empty (spec US-02 AC-1).
    Status column uses [x] for complete and [ ] for pending.
    Title and description are truncated if they exceed their column widths.
    """
    if not tasks:
        print("\n  No tasks found.")
        return

    header = (
        f"  {'ID':>{_COL_ID}}"
        f"  {'Status':<{_COL_STATUS}}"
        f"  {'Title':<{_COL_TITLE}}"
        f"  Description"
    )

    print()
    print(_TBL_HEAVY)
    print(header)
    print(_TBL_LIGHT)

    for task in tasks:
        status = STATUS_COMPLETE if task.completed else STATUS_PENDING
        title  = _truncate(task.title, _COL_TITLE)
        desc   = _truncate(task.description, _COL_DESC)
        print(
            f"  {task.id:>{_COL_ID}}"
            f"  {status:<{_COL_STATUS}}"
            f"  {title:<{_COL_TITLE}}"
            f"  {desc}"
        )

    print(_TBL_HEAVY)
    print(f"  {len(tasks)} task(s)")


# ---------------------------------------------------------------------------
# Feature handlers  (US-01 through US-05)
# ---------------------------------------------------------------------------


def handle_add(manager: TaskManager) -> None:
    """US-01 — Prompt for title and optional description, then add a task."""
    _section("Add New Task")

    title = input("  Title (required)     : ").strip()
    if not title:
        print("  Error: Title cannot be empty.")
        return
    if len(title) > MAX_TITLE_LENGTH:
        print(f"  Error: Title must be {MAX_TITLE_LENGTH} characters or fewer.")
        return

    description = input("  Description          : ").strip()
    if len(description) > MAX_DESCRIPTION_LENGTH:
        print(f"  Error: Description must be {MAX_DESCRIPTION_LENGTH} characters or fewer.")
        return

    task = manager.add_task(title, description)
    print(f"\n  Task #{task.id} added successfully.")


def handle_view(manager: TaskManager) -> None:
    """US-02 — Retrieve and display all tasks."""
    print_tasks(manager.get_all_tasks())


def handle_update(manager: TaskManager) -> None:
    """US-03 — Prompt for task ID, then optionally update title/description."""
    _section("Update Task")

    task_id = _prompt_task_id("Task ID to update")
    if task_id is None:
        return

    task = manager.get_task(task_id)
    if task is None:
        print(f"  Error: Task #{task_id} not found.")
        return

    print(f"  Current title        : {task.title}")
    new_title_raw = input("  New title            : ")
    new_title = new_title_raw.strip() or None  # None = keep existing (US-03 AC-2)

    if new_title is not None and len(new_title) > MAX_TITLE_LENGTH:
        print(f"  Error: Title must be {MAX_TITLE_LENGTH} characters or fewer.")
        return

    print(f"  Current description  : {task.description or '(none)'}")
    new_desc_raw = input("  New description      : ")
    new_desc = new_desc_raw.strip() if new_desc_raw.strip() else None  # US-03 AC-3

    if new_desc is not None and len(new_desc) > MAX_DESCRIPTION_LENGTH:
        print(f"  Error: Description must be {MAX_DESCRIPTION_LENGTH} characters or fewer.")
        return

    manager.update_task(task_id, title=new_title, description=new_desc)
    print(f"\n  Task #{task_id} updated successfully.")


def handle_delete(manager: TaskManager) -> None:
    """US-04 — Prompt for task ID, confirm, then delete."""
    _section("Delete Task")

    task_id = _prompt_task_id("Task ID to delete")
    if task_id is None:
        return

    task = manager.get_task(task_id)
    if task is None:
        print(f"  Error: Task #{task_id} not found.")
        return

    confirm = input(f"  Delete '{task.title}'? (y/n) : ").strip().lower()
    if confirm == "y":
        manager.delete_task(task_id)
        print(f"\n  Task #{task_id} deleted.")
    else:
        print("\n  Delete cancelled.")


def handle_toggle(manager: TaskManager) -> None:
    """US-05 — Prompt for task ID and flip its completion status."""
    _section("Toggle Task Status")

    task_id = _prompt_task_id("Task ID to toggle")
    if task_id is None:
        return

    task = manager.toggle_complete(task_id)
    if task is None:
        print(f"  Error: Task #{task_id} not found.")
        return

    status = "complete" if task.completed else "pending"
    print(f"\n  Task #{task_id} marked as {status}.")
