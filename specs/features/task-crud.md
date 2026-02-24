# Feature Specification: Task CRUD — Phase I Console Todo App

**Feature Branch**: `phase-1-task-crud`
**Created**: 2026-02-24
**Status**: Draft
**Stage**: spec
**Version**: 1.0.0

---

## Overview

A console-based task management feature for a Python 3.13 in-memory application. Users interact via a numbered menu. All task data lives in RAM — no file or database persistence. This is the complete feature set for Phase I.

---

## User Scenarios & Testing

### US-01 — Create Task (Priority: P1)

A user wants to capture something they need to do. They choose "Add Task" from the menu, enter a title (required), and optionally enter a description. The system assigns a unique auto-incremented integer ID and creates the task with `completed = False`.

**Why this priority**: No other operation is meaningful without tasks existing. Every other user story depends on this one.

**Independent Test**: Can be tested in isolation by running `TaskService.add_task()` and asserting the returned `Task` has the expected ID, title, description, and `completed = False`.

**Acceptance Scenarios**:

1. **Given** an empty task store, **When** the user enters a non-empty title and optional description, **Then** a `Task` is created with `id=1`, the given title, description, `completed=False`, and the system prints `"Task #1 added successfully."`
2. **Given** existing tasks, **When** a new task is added, **Then** its ID is one greater than the highest existing ID (auto-increment, no reuse).
3. **Given** the add-task prompt, **When** the user submits an empty string for title, **Then** no task is created and the system prints `"Title cannot be empty."`
4. **Given** the add-task prompt, **When** the user submits a title exceeding 200 characters, **Then** no task is created and the system prints `"Title must be 200 characters or fewer."`
5. **Given** the add-task prompt, **When** the user submits a description exceeding 500 characters, **Then** no task is created and the system prints `"Description must be 500 characters or fewer."`
6. **Given** the add-task prompt, **When** the user presses Enter with no description input, **Then** the task is created with `description = ""`.

---

### US-02 — View All Tasks (Priority: P2)

A user wants to see everything on their list. They choose "View Tasks" from the menu and receive a formatted table showing all tasks with their ID, status indicator, title, and truncated description.

**Why this priority**: The primary feedback loop for any todo app — users must see what exists before they can act on it.

**Independent Test**: Can be tested by seeding the `TaskStore` directly and calling `CLI.display_tasks()`, asserting the printed output contains the expected rows.

**Acceptance Scenarios**:

1. **Given** an empty task store, **When** the user selects "View Tasks", **Then** the system prints `"No tasks found."`
2. **Given** one or more tasks, **When** the user selects "View Tasks", **Then** each task is shown on its own row in order of ascending ID.
3. **Given** a pending task, **When** tasks are displayed, **Then** the status column shows `[    ]`.
4. **Given** a completed task, **When** tasks are displayed, **Then** the status column shows `[DONE]`.
5. **Given** a task with a description longer than 30 characters, **When** tasks are displayed, **Then** the description column shows the first 30 characters followed by `"..."`.
6. **Given** a task with a description of 30 characters or fewer, **When** tasks are displayed, **Then** the full description is shown without truncation.

**Display Format**:
```
ID   Status   Title                     Description
--   ------   -----                     -----------
1    [    ]   Buy groceries             Milk, eggs, bread...
2    [DONE]   Submit report
```

---

### US-03 — Update Task (Priority: P3)

A user realises the title or description of an existing task needs to change. They choose "Update Task", enter the task's ID, then optionally provide a new title and/or new description. Pressing Enter without input keeps the existing value.

**Why this priority**: Correction of data is important but cannot happen until tasks exist (depends on US-01).

**Independent Test**: Can be tested by creating a task, calling `TaskService.update_task()` with new values, and asserting only the changed fields differ.

**Acceptance Scenarios**:

1. **Given** a valid task ID, **When** the user enters a new title and new description, **Then** both fields are updated and the system prints `"Task #<id> updated successfully."`
2. **Given** a valid task ID, **When** the user presses Enter without typing a new title, **Then** the existing title is preserved.
3. **Given** a valid task ID, **When** the user presses Enter without typing a new description, **Then** the existing description is preserved.
4. **Given** an ID that does not exist, **When** the user attempts to update, **Then** no task is modified and the system prints `"Task #<id> not found."`
5. **Given** a valid task ID, **When** the user enters an empty string as the new title (not just Enter), **Then** the update is rejected and the system prints `"Title cannot be empty."`
6. **Given** a valid task ID, **When** the user enters a non-integer for the ID prompt, **Then** the system prints `"Please enter a valid task ID."`

---

### US-04 — Delete Task (Priority: P4)

A user wants to remove a task that is no longer relevant. They choose "Delete Task", enter the task's ID, confirm the deletion, and the task is permanently removed from the in-memory store.

**Why this priority**: Cleanup is less critical than creation and viewing; deletion depends on tasks existing.

**Independent Test**: Can be tested by creating a task, calling `TaskService.delete_task()`, then asserting `TaskStore` no longer contains that ID.

**Acceptance Scenarios**:

1. **Given** a valid task ID, **When** the user selects delete and confirms with `y`, **Then** the task is removed and the system prints `"Task #<id> deleted."`
2. **Given** a valid task ID, **When** the user selects delete and enters `n` at confirmation, **Then** the task is NOT removed and the system prints `"Delete cancelled."`
3. **Given** an ID that does not exist, **When** the user attempts to delete, **Then** nothing is removed and the system prints `"Task #<id> not found."`
4. **Given** a valid task ID, **When** the user enters a non-integer for the ID prompt, **Then** the system prints `"Please enter a valid task ID."`
5. **Given** a deleted task's ID, **When** the user views tasks, **Then** the deleted task is not present in the list.

---

### US-05 — Toggle Completion (Priority: P5)

A user wants to mark a task done (or undo it). They choose "Toggle Complete", enter the task's ID, and the system flips `completed` between `False` and `True`.

**Why this priority**: Status management is a quality-of-life feature; the core loop is functional without it.

**Independent Test**: Can be tested by creating a pending task, calling `TaskService.toggle_complete()`, asserting `completed=True`, then calling again and asserting `completed=False`.

**Acceptance Scenarios**:

1. **Given** a pending task, **When** toggle is called, **Then** `completed` becomes `True` and the system prints `"Task #<id> marked as complete."`
2. **Given** a completed task, **When** toggle is called, **Then** `completed` becomes `False` and the system prints `"Task #<id> marked as pending."`
3. **Given** an ID that does not exist, **When** toggle is called, **Then** nothing changes and the system prints `"Task #<id> not found."`
4. **Given** a non-integer ID input, **When** toggle is called, **Then** the system prints `"Please enter a valid task ID."`

---

### Edge Cases

- What happens when the store has 0 tasks and the user tries to update, delete, or toggle? → `"Task #<id> not found."` in all cases.
- What happens when a user enters whitespace-only as a title? → Treated as empty; rejected with `"Title cannot be empty."`
- What happens if the user enters an ID larger than any existing ID? → `"Task #<id> not found."`
- What happens if the user enters `0` or a negative integer as an ID? → `"Task #<id> not found."` (IDs start at 1).
- What happens when the menu receives a non-numeric input? → `"Invalid option. Please try again."`
- What happens on `KeyboardInterrupt` (Ctrl+C)? → Application exits cleanly with `"Goodbye."` — no traceback shown.

---

## Requirements

### Functional Requirements

| ID | Requirement |
|----|-------------|
| **FR-001** | System MUST allow users to add a task with a required title (1–200 chars) and optional description (0–500 chars). |
| **FR-002** | System MUST auto-generate a unique integer ID for each task, starting at 1 and incrementing by 1. IDs are never reused within a session. |
| **FR-003** | System MUST default `completed` to `False` on task creation. |
| **FR-004** | System MUST display all tasks in a table ordered by ascending ID, showing ID, status indicator, title, and truncated description. |
| **FR-005** | System MUST show `[DONE]` for completed tasks and `[    ]` for pending tasks in the status column. |
| **FR-006** | System MUST show `"No tasks found."` when the task store is empty and the user views tasks. |
| **FR-007** | System MUST allow updating a task's title and/or description by ID; pressing Enter without input preserves the existing value. |
| **FR-008** | System MUST require confirmation (`y/n`) before deleting a task. |
| **FR-009** | System MUST toggle `completed` between `True` and `False` for a given task ID. |
| **FR-010** | System MUST validate all user inputs and display a specific error message for each failure mode (see error catalogue below). |
| **FR-011** | System MUST operate entirely in memory — no file I/O, no database, no network calls. |
| **FR-012** | System MUST present a numbered console menu as the sole interface. |
| **FR-013** | System MUST handle `KeyboardInterrupt` (Ctrl+C) gracefully and exit with `"Goodbye."`. |

### Error Catalogue

| Input Error | System Response |
|-------------|----------------|
| Empty title | `"Title cannot be empty."` |
| Title > 200 chars | `"Title must be 200 characters or fewer."` |
| Description > 500 chars | `"Description must be 500 characters or fewer."` |
| Non-integer ID | `"Please enter a valid task ID."` |
| ID not found | `"Task #<id> not found."` |
| Invalid menu choice | `"Invalid option. Please try again."` |

### Key Entities

- **Task**: The core domain object. Represents a single to-do item.
  - `id: int` — positive integer, auto-assigned, unique within the session
  - `title: str` — required, 1–200 characters
  - `description: str` — optional, 0–500 characters, defaults to `""`
  - `completed: bool` — defaults to `False`

- **TaskStore**: The in-memory collection.
  - Holds all `Task` instances for the session lifetime
  - Owns the ID counter — no external code increments the counter
  - Provides lookup by ID in O(1) using a `dict[int, Task]` backing structure

---

## Success Criteria

### Measurable Outcomes

| ID | Criterion |
|----|-----------|
| **SC-001** | All five user stories (US-01 through US-05) have at least one passing pytest test for the happy path. |
| **SC-002** | All error paths listed in the Error Catalogue have at least one passing pytest test. |
| **SC-003** | `uv run todo` launches the application with a visible numbered menu within 1 second on a standard development machine. |
| **SC-004** | Each feature (add, view, update, delete, toggle) is exercisable from the menu without restarting the application. |
| **SC-005** | No unhandled exceptions are visible to the user under any valid input sequence. |
| **SC-006** | All task operations complete in under 100 ms with up to 1,000 tasks in the store (in-memory guarantee). |
| **SC-007** | No third-party packages are required — `uv run todo` works on a clean Python 3.13 install. |

---

## Technical Notes

| Concern | Decision |
|---------|----------|
| Language | Python 3.13+ |
| Runtime / Packaging | UV (`uv run todo` entry point in `pyproject.toml`) |
| Dependencies | Standard library only — no `pip install` required |
| Persistence | None — all data lives in RAM; session ends when process exits |
| Architecture | Three-layer: `CLI → TaskService → TaskStore/Task` (see `specs/constitution.md §III`) |
| Interface | Console only — no web, no GUI, no file output |
| Concurrency | Single-threaded — no async, no threads |
| ID generation | `TaskStore` owns an internal `_next_id: int` counter, incremented on every successful `add_task` call |
| Status display | `[DONE]` / `[    ]` — ASCII-safe, Windows-compatible (no Unicode symbols) |
| Test runner | `pytest` via `uv run pytest` |

---

## Out of Scope

The following are explicitly excluded from this feature and this phase:

- File or database persistence of any kind
- Sorting, filtering, or searching tasks
- Task priorities, tags, categories, or due dates
- Authentication or user sessions
- Color or rich terminal formatting
- Configuration files or environment variables
- Logging to files
- Any web or GUI interface
- Task dependencies or subtasks

---

## References

- `specs/constitution.md` — Project-wide principles and architecture rules
- `.specify/memory/constitution.md` — Broader project constitution (all phases)
- `specs/phase1-console/spec.md` — Original Phase I spec (superseded in detail by this document)
- `src/models.py` — Implementation home for `Task` and `TaskStore`
- `src/task_service.py` — Implementation home for `TaskService`
- `src/cli.py` — Implementation home for `CLI`
