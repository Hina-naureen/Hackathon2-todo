# Architecture Specification — Phase I Console Todo App

**Branch**: `master`
**Date**: 2026-02-24
**Status**: Ratified
**Spec**: `specs/features/task-crud.md`
**Constitution**: `specs/constitution.md`
**Version**: 1.0.0

---

## Summary

A single-process, in-memory Python 3.13 console application structured in three strict layers: **CLI → Service → Model**. All code is AI-generated (Claude Code); no manual coding is permitted. The architecture is deliberately thin today and explicitly designed for a future Phase II extraction path to a REST API without requiring model or service rewrites.

---

## Technical Context

| Concern | Decision |
|---------|----------|
| **Language / Version** | Python 3.13+ |
| **Package Manager** | UV (`uv run todo`) |
| **Dependencies** | Standard library only — zero third-party packages |
| **Storage** | In-memory (`dict[int, Task]` inside `TaskStore`) |
| **Testing** | `pytest` via `uv run pytest` |
| **Target Platform** | Any OS console (Windows-safe ASCII output) |
| **Performance Goal** | < 100 ms per operation at up to 1,000 tasks |
| **Concurrency** | Single-threaded; no `async`, no threads |
| **Entry Point** | `src.main:main` — declared in `pyproject.toml` |
| **Implements** | `specs/features/task-crud.md` (US-01 through US-05) |

> **Note on `task_manager.py`**: The user specification referred to this module by that name. The actual implemented module is `src/task_service.py`, which carries the `TaskService` class. This document uses `task_service.py` throughout to match the codebase exactly.

---

## Constitution Check

| Gate | Status | Evidence |
|------|--------|---------|
| No code without a spec | PASS | Spec exists at `specs/features/task-crud.md` |
| Claude Code generates all code | PASS | No manual edits; all code traces to PHRs |
| Stdlib only | PASS | `pyproject.toml` has `dependencies = []` |
| No persistence | PASS | `TaskStore` uses an in-process list/dict only |
| Three-layer import direction enforced | PASS | `cli.py → task_service.py → models.py` (verified below) |
| Secrets policy | PASS | No `.env` required; no credentials in scope |

---

## Folder Structure

```text
Hackathon2-todo/
│
├── src/                          # All application source code
│   ├── __init__.py               # Package marker (empty)
│   ├── main.py                   # Entry point — wiring + event loop
│   ├── models.py                 # Data layer: Task dataclass + TaskStore
│   ├── task_service.py           # Service layer: business logic + validation
│   └── cli.py                    # CLI layer: I/O, menus, display formatting
│
├── tests/                        # (Phase I test suite — to be created)
│   ├── test_models.py            # Unit tests for Task + TaskStore
│   ├── test_task_service.py      # Unit tests for TaskService
│   └── test_cli.py               # Integration tests for CLI handlers
│
├── specs/                        # Specification documents
│   ├── constitution.md           # Phase I binding principles
│   ├── architecture.md           # This file
│   ├── features/
│   │   └── task-crud.md          # Feature spec (US-01 to US-05)
│   └── phase1-console/           # Original Phase I docs (historical)
│       ├── spec.md
│       ├── plan.md
│       └── tasks.md
│
├── history/
│   ├── prompts/                  # Prompt History Records (PHRs)
│   │   ├── constitution/
│   │   ├── general/
│   │   └── task-crud/
│   └── adr/                      # Architecture Decision Records
│
├── .specify/
│   ├── memory/
│   │   └── constitution.md       # Global project constitution (all phases)
│   └── templates/                # Spec-Kit Plus templates
│
├── pyproject.toml                # UV project config + script entry point
├── CLAUDE.md                     # Claude Code instructions
└── README.md
```

---

## Module Breakdown

### Layer 1 — Data Layer: `src/models.py`

**Responsibility**: Define the domain object and own the in-memory store. Zero business logic. Zero I/O.

**Import rule**: Imports nothing from this project.

```python
# Canonical signature (src/models.py)

@dataclass
class Task:
    id: int
    title: str
    description: str = ""
    completed: bool = False

class TaskStore:
    _tasks: dict[int, Task]   # backing structure (O(1) lookup by ID)
    _next_id: int             # owned counter; never reset or reused

    def add(title: str, description: str = "") -> Task
    def get_all() -> list[Task]
    def get_by_id(task_id: int) -> Task | None
    def delete(task_id: int) -> bool
```

**Key decisions**:
- `Task` is a `dataclass` — lightweight, no custom `__init__` overhead, fields are mutable for in-place update.
- `TaskStore` wraps a `list[Task]` internally (current) but the public API matches a `dict`-backed interface, making a future swap to `dict[int, Task]` a one-file change.
- ID counter is owned here — no calling code may increment it directly.
- `get_all()` returns a shallow copy (`list(self._tasks)`) to prevent external mutation of the store's internal list.

**Future API migration path**: Replace the `list` backing store with a SQLModel/SQLAlchemy session call in Phase II. The `TaskStore` interface is the only boundary that changes.

---

### Layer 2 — Service Layer: `src/task_service.py`

**Responsibility**: All business logic, input validation, and domain rules. No `print`, no `input`. Returns typed results; never raises UI-level exceptions.

**Import rule**: Imports from `src.models` only.

```python
# Canonical signature (src/task_service.py)

class TaskService:
    def __init__(store: TaskStore) -> None

    def add_task(title: str, description: str = "") -> Task
        # Strips whitespace; delegates to TaskStore.add()

    def get_all_tasks() -> list[Task]
        # Delegates to TaskStore.get_all()

    def update_task(
        task_id: int,
        title: str | None = None,
        description: str | None = None,
    ) -> Task | None
        # None param = keep existing value
        # Returns None if task_id not found

    def delete_task(task_id: int) -> tuple[bool, str]
        # Returns (True, task_title) on success
        # Returns (False, "") if not found

    def toggle_complete(task_id: int) -> Task | None
        # Flips task.completed; returns None if not found
```

**Key decisions**:
- `TaskService` receives `TaskStore` via constructor injection — no global state, fully testable with a fresh store per test.
- Validation is minimal at this layer (stripping whitespace); length validation lives in the CLI layer where user input originates. This will flip in Phase II when the service becomes an API endpoint that must validate independently of the transport.
- Return types use `None` / `tuple[bool, str]` instead of exceptions — keeps the CLI layer simple and avoids exception-driven flow control for expected business conditions.

**Future API migration path**: In Phase II, `TaskService` becomes the FastAPI dependency-injectable service. Its method signatures remain unchanged; only the `TaskStore` constructor argument is swapped for a database session.

---

### Layer 3 — CLI Layer: `src/cli.py`

**Responsibility**: All console I/O — reading user input, displaying output, formatting tables. Delegates every decision to `TaskService`. Contains no business logic.

**Import rule**: Imports from `src.task_service` and `src.models` (for type hints only).

```python
# Canonical public API (src/cli.py)

def print_menu() -> None
    # Renders the numbered menu header

def print_tasks(tasks: list[Task]) -> None
    # Formats and prints the task table
    # "No tasks found." when list is empty

def handle_add(service: TaskService) -> None
    # Prompts for title + description
    # Validates length constraints before calling service

def handle_view(service: TaskService) -> None
    # Calls service.get_all_tasks(), passes to print_tasks()

def handle_update(service: TaskService) -> None
    # Prompts for ID; Enter-to-keep logic for title/description

def handle_delete(service: TaskService) -> None
    # Prompts for ID; asks y/n confirmation before delegating

def handle_toggle(service: TaskService) -> None
    # Prompts for ID; prints status message based on returned Task
```

**Display format** (80-char terminal safe):
```
========================================
         TODO APP - Phase I
========================================
  1. Add Task
  2. View All Tasks
  3. Update Task
  4. Delete Task
  5. Toggle Complete/Incomplete
  0. Exit
========================================

ID    Status       Title                     Description
--    ------       -----                     -----------
1     [    ]       Buy groceries             Milk, eggs, bread...
2     [DONE]       Submit report
```

**Status indicators**: `[DONE]` / `[    ]` — ASCII-only, Windows-compatible (no Unicode).

**Key decisions**:
- All handler functions are module-level functions (not a class). This keeps `cli.py` easily mockable in tests via `monkeypatch` and avoids unnecessary state.
- Input validation in the CLI layer (title length, non-integer IDs) is a Phase I pragmatic choice. In Phase II this moves to the service layer when it becomes an API endpoint.
- `handle_update` uses `None` sentinel to distinguish "user pressed Enter" (keep value) from "user typed something" (update value).

**Future API migration path**: `cli.py` is entirely replaced by FastAPI route handlers in Phase II. The handler pattern (`handle_*` functions calling `service.*`) directly maps to route handler → service call.

---

### Entry Point: `src/main.py`

**Responsibility**: Application bootstrap and main event loop. Wires the three layers together. Contains no logic beyond routing menu choices to handlers.

**Import rule**: Imports from all three layers for wiring only.

```python
# src/main.py — full structure

def main() -> None:
    store = TaskStore()          # instantiate store
    service = TaskService(store) # inject into service

    while True:
        print_menu()
        choice = input("Enter choice: ").strip()

        match choice:
            case "1": handle_add(service)
            case "2": handle_view(service)
            case "3": handle_update(service)
            case "4": handle_delete(service)
            case "5": handle_toggle(service)
            case "0": print("\nGoodbye!"); break
            case _:   print("Invalid option. Please try again.")
```

> Current implementation uses `if/elif` chain; a `match` statement is the clean Python 3.10+ equivalent and is valid in 3.13.

**Key decisions**:
- `main()` does no validation, no I/O formatting, and no business logic — it is a pure router.
- `KeyboardInterrupt` (Ctrl+C) should be caught here in the loop and result in a clean `"Goodbye."` exit with no traceback.
- `TaskStore` and `TaskService` are instantiated once and shared for the lifetime of the process.

---

## Component Interaction Diagram

```
User Input (stdin)
      │
      ▼
┌─────────────────────────────────────────┐
│  src/main.py — Event Loop               │
│  • Reads raw menu choice                │
│  • Routes to correct handler            │
└─────────────────┬───────────────────────┘
                  │ calls handle_*(service)
                  ▼
┌─────────────────────────────────────────┐
│  src/cli.py — CLI Layer                 │
│  • Reads/validates user input           │
│  • Formats and prints output            │
│  • Calls TaskService methods            │
└─────────────────┬───────────────────────┘
                  │ service.add_task() etc.
                  ▼
┌─────────────────────────────────────────┐
│  src/task_service.py — Service Layer    │
│  • Applies business rules               │
│  • Strips/normalises input              │
│  • Calls TaskStore methods              │
└─────────────────┬───────────────────────┘
                  │ store.add() / get_by_id() etc.
                  ▼
┌─────────────────────────────────────────┐
│  src/models.py — Data Layer             │
│  • Task dataclass                       │
│  • TaskStore (in-memory dict/list)      │
│  • ID counter                           │
└─────────────────────────────────────────┘
                  │
                  ▼
          RAM (process lifetime)
```

**Import direction** (one-way, strictly enforced):
```
main.py  →  cli.py  →  task_service.py  →  models.py
```
No reverse imports. No circular dependencies.

---

## Design Principles

### 1. Single Responsibility
Each module has exactly one reason to change:

| Module | Changes when... |
|--------|----------------|
| `models.py` | The `Task` schema changes or storage backing changes |
| `task_service.py` | Business rules or validation logic changes |
| `cli.py` | The console UI, prompts, or display format changes |
| `main.py` | The top-level event loop or wiring changes |

### 2. Modular Code
- Each layer is independently importable and independently testable.
- `TaskService` can be tested with a freshly instantiated `TaskStore` — no global fixtures needed.
- `CLI` handlers can be tested with `monkeypatch` on `builtins.input` and `builtins.print`.
- Replacing any layer requires changing only the adjacent layer's import.

### 3. Easy Future API Migration (Phase II Path)
The architecture is explicitly designed for extraction:

| Phase I | Phase II Replacement |
|---------|---------------------|
| `TaskStore` (list/dict) | SQLModel session + Neon DB |
| `TaskService` (unchanged) | FastAPI dependency — same signatures |
| `cli.py` handlers | FastAPI route handlers — same pattern |
| `main.py` loop | FastAPI `app` + Uvicorn server |
| `uv run todo` | `uv run uvicorn src.api:app` |

The service layer interface is the **API contract** between Phase I and Phase II. No Phase II work should require changes to `task_service.py`.

### 4. AI-Generated Implementation Only
- No line of implementation code is written by a human.
- Claude Code generates all source from spec acceptance criteria.
- The human architect writes specs, reviews outputs, and approves diffs.
- Every generation session is recorded in a PHR under `history/prompts/`.

---

## Error Handling Architecture

```
User Input
    │
    ▼
CLI Layer          ← catches: empty title, non-integer ID,
    │                          over-length strings
    │ ValueError / None check
    ▼
Service Layer      ← returns: None (not found), False (delete failed)
    │                          never raises on expected business conditions
    │ None / (bool, str)
    ▼
Data Layer         ← returns: None (get_by_id miss), False (delete miss)
                               never raises

Top-level (main.py):
    KeyboardInterrupt → print("Goodbye.") → sys.exit(0)
    Unexpected Exception → print("An unexpected error occurred.") → continue
```

**Rule**: Exceptions propagate upward only for truly unexpected failures. Expected conditions (ID not found, validation failure) use return-value signalling.

---

## Testing Architecture

```text
tests/
├── test_models.py         # Unit — TaskStore isolation, ID counter, get/delete
├── test_task_service.py   # Unit — TaskService with fresh TaskStore per test
└── test_cli.py            # Integration — monkeypatch stdin/stdout, full handler paths
```

**Test naming**: `test_<unit>_<scenario>_<expected_outcome>`

**Isolation rule**: Each test instantiates its own `TaskStore`. No shared state between tests.

**Run command**: `uv run pytest tests/ -v`

---

## Complexity Justification

| Decision | Why Needed | Simpler Alternative Rejected Because |
|----------|-----------|--------------------------------------|
| Three-layer separation | Enables Phase II API extraction without rewriting service logic | Two-layer (service + CLI merged) would require a full rewrite in Phase II |
| Constructor injection for `TaskStore` | Enables isolated unit testing of `TaskService` | Global `TaskStore` singleton would make tests stateful and order-dependent |
| `None` return over exceptions | Keeps CLI control flow simple and readable | `TaskNotFoundError` exception adds boilerplate with no benefit at this scale |

---

## Out of Scope — Phase I

Not to be introduced in this phase under any circumstances:

- Database, file, or network I/O
- `async` / `await` or threading
- Third-party libraries
- Pydantic or SQLModel models
- Authentication or session state
- Web framework (FastAPI, Flask, etc.)
- Logging to files or external services
- Configuration management (`.env`, `settings.py`)

---

## References

| Document | Path |
|----------|------|
| Project constitution | `specs/constitution.md` |
| Global constitution (all phases) | `.specify/memory/constitution.md` |
| Feature spec | `specs/features/task-crud.md` |
| Original Phase I plan | `specs/phase1-console/plan.md` |
| Entry point | `src/main.py` |
| Data layer | `src/models.py` |
| Service layer | `src/task_service.py` |
| CLI layer | `src/cli.py` |
| Project config | `pyproject.toml` |

---

---

# Architecture Specification — Phase II: Full-Stack Web API

**Added:** 2026-02-28
**Status:** Implemented
**Spec:** `specs/features/task-crud.md`, `specs/features/authentication.md`, `specs/api/rest-endpoints.md`

---

## Summary

Phase II extracts the Phase I service layer into a FastAPI web backend and adds a Next.js frontend. The `TaskManager` class is unchanged. The only change at the data layer is swapping `TaskStore` for `DBTaskStore`, which implements the same interface against a SQLModel/Neon PostgreSQL session. JWT-based authentication enforces per-user task isolation at every endpoint.

---

## Phase II Layer Diagram

```
Browser (Next.js :3000)
        │
        │  HTTPS — fetch() with Authorization: Bearer <JWT>
        ▼
┌──────────────────────────────────────────────────────┐
│  Next.js App Router (frontend/)                      │
│                                                      │
│  middleware.ts  ←── JWT edge guard (jose)            │
│  app/(auth)/    ←── sign-in / sign-up pages          │
│  app/tasks/     ←── task list page                   │
│  components/    ←── TaskList, ChatPanel, Header      │
│  lib/api.ts     ←── typed fetch wrapper              │
│  lib/user-store ←── scrypt user store (file-based)   │
└──────────────────────────────────────────────────────┘
        │
        │  REST — Authorization: Bearer <JWT>
        ▼
┌──────────────────────────────────────────────────────┐
│  FastAPI (backend/src/app.py :8000)                  │
│                                                      │
│  src/auth/dependencies.py  ←── get_current_user()   │
│  src/routes/tasks.py       ←── CRUD endpoints        │
│  src/routes/auth.py        ←── register / login      │
│  src/routes/chat.py        ←── AI chat endpoint      │
│                                                      │
│  src/task_manager.py   ←── Phase I service (UNCHANGED)│
│  src/database.py       ←── DBTaskStore + engine      │
│  src/db_models.py      ←── SQLModel Task table       │
│                                                      │
│  Alembic migrations    ←── alembic/versions/         │
└──────────────────────────────────────────────────────┘
        │
        │  SQLAlchemy — NullPool (Neon pooler)
        ▼
┌──────────────────────────────────────────────────────┐
│  Neon PostgreSQL (eu-central-1)                      │
│  task table — 7 columns + ix_task_user_id index      │
└──────────────────────────────────────────────────────┘
```

## Key Phase II Decisions

| Decision | Rationale |
|----------|-----------|
| `TaskManager` unchanged | Phase I–II contract: service layer is transport-agnostic |
| `DBTaskStore` adapter | Implements same `TaskStore` interface; injected via constructor |
| `NullPool` for Neon pooler | PgBouncer + SQLAlchemy QueuePool = double-pooling; NullPool delegates to PgBouncer |
| JWT shared secret | Stateless auth; `BETTER_AUTH_SECRET` shared between FastAPI (PyJWT) and Next.js edge (jose) |
| File-based user store | Simplest viable auth for hackathon; not production-grade |
| Alembic migrations | Version-controlled schema; `upgrade head` runs on container startup |

## Phase II Layer Import Rules

```
Next.js                      FastAPI
──────                       ───────
middleware.ts                app.py → routes/* → task_manager.py → DBTaskStore → Session
lib/api.ts (fetch only)                       ↑
                             auth/dependencies.py (JWT → user_id)
```

No component imports directly from the backend. All data access is through `lib/api.ts` fetch calls.

---

---

# Architecture Specification — Phase III: AI Agent Layer

**Added:** 2026-03-01
**Status:** Implemented
**Spec:** `specs/features/chatbot.md`, `specs/api/mcp-tools.md`, `specs/agents/agent-behavior.md`

---

## Summary

Phase III adds an agentic AI layer on top of the Phase II REST API. The agent receives natural language from the user, decides which tool(s) to invoke, executes them, and returns a natural-language reply. Tools call `TaskManager` in-process (not via HTTP) using the same validated `user_id` and `Session` that the REST routes use.

---

## Phase III Layer Diagram

```
Browser
  │
  │  POST /api/chat  { "message": "add a task to buy milk" }
  │  Authorization: Bearer <JWT>
  ▼
┌────────────────────────────────────────────────────────────┐
│  ChatPanel.tsx (frontend/components/)                      │
│  · Sends JWT + message to POST /api/chat                   │
│  · Calls onMutation() when mutation tools ran              │
│  · Falls back to local simulateAI() on network error       │
└────────────────────────────────────────────────────────────┘
  │
  │  POST /api/chat (FastAPI route)
  ▼
┌────────────────────────────────────────────────────────────┐
│  src/routes/chat.py                                        │
│  · Validates JWT → user_id                                 │
│  · Validates message (400 if empty)                        │
│  · Instantiates TaskAgent(session, user_id)                │
└────────────────────────────────────────────────────────────┘
  │
  │  agent.run(message) → (reply, actions)
  ▼
┌────────────────────────────────────────────────────────────┐
│  agents/agent.py — TaskAgent (agentic loop, max 5 iters)  │
│                                                            │
│  _call_llm(messages)                                       │
│    · OPENAI_API_KEY set   → OpenAI gpt-4o-mini             │
│    · key not set          → _local_simulate() (keyword)    │
│                                                            │
│  stop_reason="tool_calls" → call_tool() for each          │
│  stop_reason="stop"       → return reply                   │
└────────────────────────────────────────────────────────────┘
  │
  │  call_tool(session, user_id, tool_name, args)
  ▼
┌────────────────────────────────────────────────────────────┐
│  agents/tools.py — 5 tool functions                        │
│                                                            │
│  create_task  · list_tasks  · update_task                  │
│  delete_task  · toggle_complete                            │
│                                                            │
│  All scoped to user_id — no cross-user access possible     │
└────────────────────────────────────────────────────────────┘
  │
  │  TaskManager(DBTaskStore(session, user_id))
  ▼
┌────────────────────────────────────────────────────────────┐
│  src/task_manager.py (Phase I — UNCHANGED)                 │
│  + src/database.py — DBTaskStore + Neon PostgreSQL         │
└────────────────────────────────────────────────────────────┘
```

## Key Phase III Decisions

| Decision | Rationale |
|----------|-----------|
| Tools call `TaskManager` in-process | Avoids internal HTTP round-trip; identical business logic and auth as REST routes |
| `user_id` always injected, never from LLM output | Prevents prompt injection from escalating privileges |
| `_local_simulate()` fallback | Demo remains live without an OpenAI key |
| `_MAX_ITERATIONS = 5` | Prevents runaway tool-call loops; cost and latency guardrail |
| Tool errors returned as `{"error": "..."}` dicts | Agent communicates errors in natural language; no HTTP 5xx for expected conditions |
| Frontend calls `onMutation()` on mutation tools | Task list auto-refreshes after AI creates/updates/deletes a task |

## Phase III Data Flow (end-to-end)

```
User types: "delete task 3"
    │
    ▼ ChatPanel.tsx → POST /api/chat { message: "delete task 3" }
    │                 Authorization: Bearer eyJ...
    ▼ chat.py validates JWT → user_id = "abc123"
    ▼ TaskAgent.run("delete task 3")
    ▼ _call_llm → OpenAI → stop_reason="tool_calls" → delete_task(id=3)
    ▼ call_tool → delete_task(session, "abc123", id=3)
    ▼ TaskManager.delete_task(3) → DBTaskStore.delete(3) → DELETE FROM task
    ▼ Tool returns {"deleted": true, "id": 3, "title": "Buy milk"}
    ▼ _call_llm → OpenAI → stop_reason="stop"
    ▼ reply = "Done! I've deleted task #3 'Buy milk'."
    ▼ ChatResponse { reply, trace_id, actions: [{tool: "delete_task", ...}] }
    ▼ ChatPanel sees mutation tool in actions → calls onMutation()
    ▼ Task list refreshes. "Buy milk" is gone.
```

## Phase III Files

| File | Role |
|------|------|
| `backend/agents/agent.py` | `TaskAgent` — agentic loop, `LLMMessage`, `ActionTrace` |
| `backend/agents/tools.py` | 5 tool functions, `TOOL_REGISTRY`, `TOOL_SCHEMAS`, `call_tool` |
| `backend/agents/prompts.py` | `SYSTEM_PROMPT` — agent personality and tool-use rules |
| `backend/src/routes/chat.py` | `POST /api/chat` — validates, runs agent, returns `ChatResponse` |
| `frontend/components/ChatPanel.tsx` | Chat UI — sends JWT + message, handles reply + mutations |
