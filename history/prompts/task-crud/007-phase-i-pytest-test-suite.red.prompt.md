---
id: "007"
title: Phase I Pytest Test Suite
stage: red
date: 2026-02-24
surface: agent
model: claude-sonnet-4-6
feature: task-crud
branch: master
user: pc
command: "Read Phase I specs and create Pytest tests"
labels: ["red","tests","pytest","phase-1","task-crud","unit","integration","cli"]
links:
  spec: specs/features/task-crud.md
  ticket: null
  adr: null
  pr: null
files:
  - pyproject.toml
  - tests/__init__.py
  - tests/conftest.py
  - tests/test_models.py
  - tests/test_task_manager.py
  - tests/test_cli.py
tests:
  - "107 tests collected, 107 passed, 0 failed (pytest 9.0.2, Python 3.13.1)"
---

## Prompt

Read Phase I specs and create Pytest tests.

Requirements:
- Create tests folder
- test_add_task
- test_delete_task
- test_update_task
- test_list_tasks
- test_toggle_complete

Rules:
- No database
- Use in-memory data
- Clean pytest structure
- Python 3.13 compatible

Generate all tests now.

## Response snapshot

Added pytest 9.0.2 as dev dependency via [dependency-groups] in pyproject.toml.
Added [tool.pytest.ini_options] testpaths = ["tests"].

Created 5 files:

### tests/conftest.py
- `store()` fixture — fresh TaskStore, no shared state
- `manager(store)` fixture — TaskManager wired to fresh store
- `populated_manager(manager)` fixture — 3 pre-seeded tasks for view/list tests
- `make_inputs(*responses)` helper — returns an input() mock that yields responses in order

### tests/test_models.py  (66 tests)
- TestConstants: 4 tests — constants are correct types and values
- TestTask: 6 tests — dataclass defaults and explicit values
- TestTaskStoreAdd: 7 tests — id assignment, increment, no reuse after delete, unique ids
- TestTaskStoreGetAll: 4 tests — empty, count, ascending order, shallow copy
- TestTaskStoreGetById: 4 tests — found, correct among many, not found, empty store
- TestTaskStoreDelete: 6 tests — returns True/False, removes task, count, no side effects, idempotent

### tests/test_task_manager.py  (44 tests across 5 classes)
- TestAddTask (US-01): 9 tests — id increment, whitespace strip, completed=False default
- TestListTasks (US-02): 7 tests — empty list, count, ascending order, get_task by id
- TestUpdateTask (US-03): 11 tests — title/desc update, None keeps existing, empty string keeps existing, strips whitespace, returns None on missing id, does not affect other tasks
- TestDeleteTask (US-04): 7 tests — returns (True, title), (False, ""), removes task, count, no side effects, empty store
- TestToggleComplete (US-05): 6 tests — pending→complete, complete→pending, None on missing, returns task, persists, no side effects

### tests/test_cli.py  (37 tests across 5 classes)
- TestHandleAdd (US-01): 8 tests — success message, description stored, empty title error, whitespace title error, title too long, description too long
- TestHandleView (US-02): 7 tests — no tasks found, titles visible, [x]/[ ] status icons, task count, truncation "..", full short description
- TestHandleUpdate (US-03): 7 tests — updates title, success message, Enter keeps title, Enter keeps desc, id not found, non-integer id, enter keeps desc
- TestHandleDelete (US-04): 7 tests — confirmed removes, prints deleted, cancelled keeps, prints cancelled, id not found, non-integer id, no side effects on other tasks
- TestHandleToggle (US-05): 7 tests — pending→complete state, complete→pending state, prints "complete", prints "pending", id not found, non-integer id, no side effects

## Outcome

- ✅ Impact: 107/107 tests pass; all 5 US acceptance criteria covered at unit and integration level; every error catalogue path tested
- 🧪 Tests: 107 passed, 0 failed — pytest 9.0.2, Python 3.13.1, 0.69s
- 📁 Files: pyproject.toml (dev deps + pytest config), tests/__init__.py, tests/conftest.py, tests/test_models.py, tests/test_task_manager.py, tests/test_cli.py
- 🔁 Next prompts: Phase II — REST API with FastAPI + SQLModel + Neon DB
- 🧠 Reflection: Fresh fixture per test ensures full isolation; make_inputs() helper keeps CLI tests readable; all spec acceptance criteria map directly to named test functions

## Evaluation notes (flywheel)

- Failure modes observed: none — all 107 tests green on first run
- Graders run and results (PASS/FAIL): pytest 107/107 PASS
- Prompt variant (if applicable): initial
- Next experiment: add coverage reporting (`uv add --dev pytest-cov`) to verify 100% line coverage of task_manager.py
