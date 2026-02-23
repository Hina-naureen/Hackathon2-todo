# Phase I Tasks

## T-001: Create Task dataclass and TaskStore
**File:** `src/models.py`
**Description:** Define `Task` dataclass with id, title, description, completed fields. Define `TaskStore` class with in-memory list and auto-increment counter.
**Done when:** Task can be created and stored; TaskStore can add/get/delete tasks.

## T-002: Implement task service functions
**File:** `src/task_service.py`
**Description:** Implement all 5 operations: add_task, get_all_tasks, update_task, delete_task, toggle_complete.
**Done when:** All functions work correctly with TaskStore; invalid IDs return None/False.

## T-003: Implement CLI display functions
**File:** `src/cli.py`
**Description:** Menu display, task table formatter, input prompts for each operation, confirmation dialogs.
**Done when:** Menu shows correctly; task list shows formatted table; all input handlers collect and validate user input.

## T-004: Implement main entry point
**File:** `src/main.py`
**Description:** Main loop that shows menu, reads user choice, calls appropriate handler, loops until user exits.
**Done when:** App runs end-to-end; all 5 features accessible from menu; exit works cleanly.

## T-005: Update pyproject.toml and README
**Files:** `pyproject.toml`, `README.md`
**Description:** Set entry point script in pyproject.toml. Write README with setup and run instructions.
**Done when:** `uv run todo` launches the app.
