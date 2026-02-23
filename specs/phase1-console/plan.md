# Phase I Plan: Architecture & Implementation Design

## Component Breakdown

### 1. Data Layer (`src/models.py`)
- `Task` dataclass with fields: id, title, description, completed
- `TaskStore` class: in-memory list of tasks + ID counter

### 2. Service Layer (`src/task_service.py`)
- `add_task(title, description)` → Task
- `get_all_tasks()` → list[Task]
- `update_task(id, title, description)` → Task | None
- `delete_task(id)` → bool
- `toggle_complete(id)` → Task | None

### 3. UI Layer (`src/cli.py`)
- Menu display function
- Input handlers for each operation
- Formatted table output for task list
- User prompts and confirmation dialogs

### 4. Entry Point (`src/main.py`)
- Main loop
- Instantiate TaskStore
- Route menu choices to handlers

## File Structure
```
src/
├── main.py          # Entry point + main loop
├── models.py        # Task dataclass + TaskStore
├── task_service.py  # Business logic
└── cli.py           # UI / display functions
```

## Key Design Decisions

### In-Memory Storage
Use a simple Python list inside `TaskStore`. No external libraries needed.

### Auto-increment ID
`TaskStore` maintains a counter that increments on every `add_task` call. IDs are never reused.

### Separation of Concerns
- Models: pure data, no logic
- Service: business logic, no UI
- CLI: display only, calls service
- Main: wires everything together
