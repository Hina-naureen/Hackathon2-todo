---
id: "004"
title: Phase I Implementation - Green Pass
stage: green
date: 2026-02-24
surface: agent
model: claude-sonnet-4-6
feature: task-crud
branch: master
user: pc
command: "Implement Phase I Todo Console Application"
labels: ["green","implementation","phase-1","task-crud","python","cli","task-manager"]
links:
  spec: specs/features/task-crud.md
  ticket: null
  adr: null
  pr: null
files:
  - src/models.py
  - src/task_manager.py
  - src/cli.py
  - src/main.py
tests:
  - "smoke: uv run todo (boot + exit)"
  - "smoke: all 5 feature handlers (add, view, toggle, update, delete)"
  - "smoke: all error paths (empty title, non-integer ID, ID not found, empty store)"
---

## Prompt

Read and follow:
@specs/constitution.md
@specs/architecture.md
@specs/features/task-crud.md

Now implement Phase I Todo Console Application.

Rules:
- Follow Spec-Driven Development
- Do not add extra features
- Create code inside /src
- Python 3.13 compatible
- Clean CLI interface

Required structure:
src/
 main.py
 cli.py
 models.py
 task_manager.py

Features:
- Add task
- List tasks
- Update task
- Delete task
- Toggle completion

Generate full implementation now.

## Response snapshot

Rewrote all four src modules from spec. Deleted task_service.py, created task_manager.py.

### src/models.py
- Added 5 constants (MAX_TITLE_LENGTH=200, MAX_DESCRIPTION_LENGTH=500, DISPLAY_DESCRIPTION_LIMIT=30, STATUS_COMPLETE, STATUS_PENDING)
- Upgraded TaskStore backing store from list[Task] to dict[int, Task] (O(1) lookup, per architecture spec)
- get_all() returns sorted(values, key=id) for guaranteed ascending order
- Full docstrings on all public members

### src/task_manager.py (new — replaces task_service.py)
- TaskManager class with constructor injection of TaskStore
- 5 methods: add_task, get_all_tasks, get_task, update_task, delete_task, toggle_complete
- Return-value signalling: None / (bool, str) — no exceptions for expected business conditions
- None sentinel in update_task means "keep existing value" (US-03 Enter-to-keep behaviour)

### src/cli.py
- Imports TaskManager from task_manager (not task_service)
- Imports all 5 constants from models
- Layout constants for column widths (_MENU_WIDTH, _TABLE_WIDTH, etc.)
- _truncate() helper replaces inline slice logic
- _prompt_task_id() helper centralises ID validation (non-digit + <1 rejection)
- handle_add: validates empty title, title length, description length
- handle_view: delegates fully to print_tasks()
- handle_update: Enter-to-keep via None sentinel; validates new lengths before calling manager
- handle_delete: confirmation flow y/n; delegates delete to manager
- handle_toggle: flips status; prints "complete" or "pending" based on returned task

### src/main.py
- Imports TaskManager (not TaskService)
- KeyboardInterrupt caught in loop → prints "Goodbye!" → sys.exit(0)
- Unexpected Exception caught → prints message → continues loop (no traceback exposed)
- ASCII-safe "Welcome to Todo App - Phase I" (em-dash replaced with hyphen)

### Deleted
- src/task_service.py (superseded by task_manager.py)

## Outcome

- ✅ Impact: All 5 US-01–US-05 features operational; all error catalogue paths verified
- 🧪 Tests: Smoke tests passed — boot, all features, all error paths
- 📁 Files: src/models.py (rewritten), src/task_manager.py (created), src/cli.py (rewritten), src/main.py (rewritten), src/task_service.py (deleted)
- 🔁 Next prompts: Write unit tests (test_models.py, test_task_manager.py, test_cli.py) using pytest
- 🧠 Reflection: All code traces directly to spec acceptance criteria; no extra features added; Windows ASCII-safe output confirmed

## Evaluation notes (flywheel)

- Failure modes observed: em-dash (—) rendered as ? on Windows console — fixed by replacing with ASCII hyphen in main.py and cli.py
- Graders run and results (PASS/FAIL): smoke PASS — all 5 features + all 6 error catalogue paths
- Prompt variant (if applicable): initial
- Next experiment: write pytest test suite mapping each US-XX acceptance criterion to a named test function
