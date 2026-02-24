---
id: "006"
title: CLI Visual Refactor - Professional Layout
stage: refactor
date: 2026-02-24
surface: agent
model: claude-sonnet-4-6
feature: task-crud
branch: master
user: pc
command: "Refactor CLI to look professional with numbered menu and clear status icons"
labels: ["refactor","cli","visual","layout","menu","status-icons","phase-1"]
links:
  spec: specs/features/task-crud.md
  ticket: null
  adr: null
  pr: null
files:
  - src/models.py
  - src/cli.py
  - src/main.py
tests:
  - "smoke: boot + exit"
  - "smoke: add 2 tasks, view ([ ] icons), toggle task 1, view ([x] icon)"
---

## Prompt

Refactor CLI to look professional with numbered menu and clear status icons.

## Response snapshot

### src/models.py
- `STATUS_COMPLETE = "[x]"` (was `"[DONE]"`)
- `STATUS_PENDING  = "[ ]"` (was `"[    ]"`)
- Classic checkbox metaphor, symmetric 3-char icons, ASCII-safe

### src/cli.py  (visual overhaul — zero logic changes)
New layout constants:
- `_BOX_W = 44` — inner width of menu box
- `_BOX_TOP / _BOX_MID` — pre-built border strings (avoid per-render recompute)
- `_COL_ID=4, _COL_STATUS=6, _COL_TITLE=26, _COL_DESC=22` — table columns
- `_TBL_W=64` — total table content width; `_TBL_HEAVY/LIGHT` — table border strings
- `_SEC_LINE` — section operation underline
- `_MENU_ITEMS` — ordered tuple of (key, label) pairs; single source of truth for menu

New helpers:
- `_box_row(text)` — formats a single left-aligned menu box row
- `_section(title)` — prints `>> Title` + underline before each operation

`print_menu()`:
- Full box: `+----+` top/bottom, `|    |` sides, blank spacer rows
- `[N]` item numbers instead of `N.`
- Title centered via `.center(_BOX_W)`

`print_tasks()`:
- Heavy `===` borders top and bottom
- Light `---` separator under header
- Right-aligned ID column; `[x]`/`[ ]` status column with 6-char padding
- `"N task(s)"` footer below heavy border

All handlers:
- `_section()` call for consistent operation header
- Aligned input labels (same column width within each operation)
- Two-space indent on all print statements
- `_prompt_task_id()` label now uses `{label:<20}` for alignment

### src/main.py
- Welcome: `"  Todo App  -  Phase I  |  Press Ctrl+C to exit"`
- Prompt: `"  Enter choice [0-5]   : "`
- Goodbye: `"  Goodbye!"`
- Invalid option: `"  Invalid option. Please try again."`

## Outcome

- ✅ Impact: Visually professional terminal UI; menu box clearly frames choices; `[x]`/`[ ]` icons immediately scannable; all outputs consistently indented
- 🧪 Tests: Smoke PASS — add × 2, view ([ ] both), toggle task 1, view ([x] task 1)
- 📁 Files: src/models.py (status constants), src/cli.py (full visual rewrite), src/main.py (prompts and messages)
- 🔁 Next prompts: Write pytest test suite — unit tests for models and task_manager, integration tests for CLI handlers
- 🧠 Reflection: Pure presentation refactor — logic unchanged, all spec acceptance criteria still satisfied; pre-built border strings are a minor perf win over string multiply per render

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): smoke PASS
- Prompt variant (if applicable): initial
- Next experiment: N/A — visual refactor complete; focus next on test coverage
