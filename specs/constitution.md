# Phase I Constitution — Spec-Driven Console Todo App

**Version:** 1.0.0
**Ratified:** 2026-02-24
**Scope:** Phase I — In-Memory Python Console Application

---

## I. Project Principles

### 1. Spec-Driven Development is Non-Negotiable
No line of code exists without a corresponding spec. Every feature follows this exact lifecycle:

```
Specify → Plan → Tasks → Red (test first) → Green (implement) → Refactor
```

The spec is the single source of truth. If the spec and the code disagree, the spec wins — fix the code.

### 2. Claude Code Generates All Code
Manual coding is **FORBIDDEN**. The human architect's role is to:
- Write specs and acceptance criteria
- Review and approve plans
- Validate test results
- Make architectural decisions (recorded in ADRs)

Claude Code's role is to:
- Generate implementation from specs
- Write tests before writing implementation
- Propose refactors with justification
- Record all work in PHRs

### 3. Simplicity Over Cleverness
YAGNI — You Aren't Gonna Need It. Do not implement Phase II features in Phase I. Each layer of abstraction must be justified by an existing requirement, not a hypothetical future one.

### 4. Smallest Viable Diff
Every change must be the minimum necessary to satisfy the acceptance criteria. No speculative features, no "nice to have" additions, no preemptive refactors.

---

## II. Coding Constraints

### Language and Runtime
- **Language:** Python 3.13+
- **Package Manager:** UV (no pip, no poetry, no conda)
- **Dependencies:** Standard library only (no third-party packages)
- **Entry Point:** `uv run todo` via `pyproject.toml` script

### Python Code Rules
| Rule | Requirement |
|------|-------------|
| Type hints | Required on all function signatures |
| Docstrings | Required on all public functions and classes |
| Max line length | 88 characters (Black-compatible) |
| Naming | `snake_case` for functions/variables, `PascalCase` for classes, `UPPER_CASE` for constants |
| Return types | All functions must declare return type (use `None` explicitly) |
| Magic numbers | FORBIDDEN — use named constants |
| Bare `except` | FORBIDDEN — always catch specific exceptions |
| `print` in business logic | FORBIDDEN — only in CLI layer |

### Forbidden Patterns
- No `global` variables
- No mutable default arguments (`def f(x=[])`)
- No wildcard imports (`from module import *`)
- No `eval()` or `exec()`
- No secrets or tokens hardcoded anywhere

---

## III. Architecture Rules

### Layer Boundaries (STRICT)
```
┌─────────────────────────────┐
│         CLI Layer           │  src/cli.py
│  (input/output, no logic)   │
├─────────────────────────────┤
│      Service Layer          │  src/task_service.py
│  (business logic, validation)│
├─────────────────────────────┤
│       Model Layer           │  src/models.py
│  (data structures, storage) │
└─────────────────────────────┘
```

**Rule:** A lower layer NEVER imports from a higher layer.
- `models.py` imports nothing from `task_service.py` or `cli.py`
- `task_service.py` imports from `models.py` only
- `cli.py` imports from `task_service.py` and `models.py`

### Single Responsibility
Each module has exactly one reason to change:
- `models.py` — Task data structure and in-memory store
- `task_service.py` — Business rules and validation
- `cli.py` — User interaction and display formatting
- `main.py` — Application entry point and wiring only

### In-Memory Storage Rules
- `TaskStore` is the single in-process data store (a `dict[int, Task]`)
- No file I/O, no pickling, no persistence of any kind
- Store lives for the duration of one process run only
- ID counter is managed by `TaskStore`, not by calling code

### No Dependency Injection Frameworks
Use plain Python. Pass dependencies as constructor arguments where needed. No IoC containers.

---

## IV. Naming Conventions

### Files
| File | Purpose |
|------|---------|
| `src/main.py` | Entry point — wires components, starts loop |
| `src/models.py` | `Task` dataclass + `TaskStore` class |
| `src/task_service.py` | `TaskService` class with all business operations |
| `src/cli.py` | `CLI` class with all console I/O |
| `tests/test_models.py` | Unit tests for models layer |
| `tests/test_task_service.py` | Unit tests for service layer |
| `tests/test_cli.py` | Integration tests for CLI layer |

### Classes
| Class | Location | Responsibility |
|-------|----------|---------------|
| `Task` | `models.py` | Immutable-ish data container |
| `TaskStore` | `models.py` | In-memory collection + ID generation |
| `TaskService` | `task_service.py` | All CRUD + toggle operations |
| `CLI` | `cli.py` | Menu, prompts, display |

### Method Naming (TaskService)
```python
add_task(title: str, description: str = "") -> Task
get_all_tasks() -> list[Task]
get_task(task_id: int) -> Task | None
update_task(task_id: int, title: str | None, description: str | None) -> Task
delete_task(task_id: int) -> bool
toggle_complete(task_id: int) -> Task
```

### Constants (in `models.py`)
```python
MAX_TITLE_LENGTH = 200
MAX_DESCRIPTION_LENGTH = 500
DISPLAY_DESCRIPTION_LIMIT = 30
STATUS_COMPLETE = "[DONE]"
STATUS_PENDING = "[    ]"
```

---

## V. Testing Philosophy

### Test-First Mandate
Tests are written **before** implementation. Every acceptance criterion in a spec maps to at least one test case. No implementation without a failing test first.

### Testing Layers
| Layer | Test Type | Tool |
|-------|-----------|------|
| Models | Unit | `pytest` (stdlib `unittest` acceptable) |
| Service | Unit | `pytest` with mocked store |
| CLI | Integration | `pytest` with captured `stdin`/`stdout` |

### Test Naming Convention
```
test_<unit_under_test>_<scenario>_<expected_outcome>
```
Examples:
- `test_add_task_with_empty_title_raises_value_error`
- `test_toggle_complete_on_pending_task_marks_done`
- `test_delete_task_with_invalid_id_returns_false`

### Coverage Requirement
- All acceptance criteria from the spec must have a corresponding passing test
- Happy path + at least one error/edge-case path per feature
- No tests that only assert `True` or pass without an actual assertion

### Test Isolation
- Each test creates its own `TaskStore` instance — no shared state between tests
- No file system access in tests
- No `time.sleep()` in tests

---

## VI. Claude Code Usage Guidelines

### Session Start Protocol
At the start of every Claude Code session:
1. Re-read `specs/constitution.md` (this file)
2. Re-read `.specify/memory/constitution.md`
3. Re-read the relevant phase spec before touching any code
4. Check `history/prompts/` for prior context on this feature

### Prompt Discipline
- One concern per prompt — do not mix "write tests" with "implement feature" in a single prompt
- Always state which spec/user story the prompt is implementing
- Reference file paths and line numbers in all responses
- Never ask Claude Code to "just write the whole app" — use the task list

### PHR Creation (Automatic)
After every significant prompt, Claude Code creates a Prompt History Record under `history/prompts/`. PHRs are NOT optional.

### ADR Triggers
Suggest an ADR when any decision meets ALL three criteria:
1. Long-term consequences (affects future phases or architecture)
2. Multiple viable alternatives were considered
3. Cross-cutting scope (affects more than one module)

### What Claude Code Must Never Do
- Write code that has no corresponding spec acceptance criterion
- Skip the Red (failing test) phase and go straight to Green
- Refactor code that is not covered by tests
- Create files outside the established project structure
- Hardcode any values that belong in constants or config
- Merge concerns across layers (e.g., validation in `cli.py`)

---

## VII. Error Handling Contract

### Validation Errors
- Raised by `TaskService` as `ValueError` with a human-readable message
- Caught by `CLI` layer and printed to console — never propagated to the user as a traceback

### ID Not Found
- `TaskService` returns `None` (get) or `False` (delete) — never raises on missing ID
- `CLI` checks the return value and displays the appropriate error message

### Unexpected Errors
- Caught at the top-level `main.py` loop
- Print: `"An unexpected error occurred: <message>. Please restart."`
- Do not swallow exceptions silently

---

## VIII. Out of Scope for Phase I

The following are explicitly **FORBIDDEN** in Phase I implementation:

- File or database persistence
- Network I/O of any kind
- Authentication or user accounts
- Task priorities, tags, or due dates
- Sorting, filtering, or searching
- Color output or rich terminal formatting
- Configuration files
- Logging to files
- Any web interface

Implementing any of the above violates this constitution and requires a formal amendment.

---

## IX. Governance

- This constitution supersedes all other documents, including internal preferences
- Amendments require documentation and explicit user approval
- ADRs are the mechanism for recording exceptions to these rules
- All implementations must comply with the active phase's spec and this constitution
- Constitution version must be incremented on every amendment

---

*Ratified for Phase I — Evolution of Todo Hackathon II*
*Scope terminates when Phase II begins; a new phase-specific constitution section will be appended.*
