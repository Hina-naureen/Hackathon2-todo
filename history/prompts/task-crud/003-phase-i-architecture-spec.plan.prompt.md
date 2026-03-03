---
id: "003"
title: Phase I Architecture Specification
stage: plan
date: 2026-02-24
surface: agent
model: claude-sonnet-4-6
feature: task-crud
branch: master
user: pc
command: "Create architecture specification at specs/architecture.md"
labels: ["architecture","plan","phase-1","task-crud","three-layer","modular","api-migration"]
links:
  spec: specs/features/task-crud.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/architecture.md
  - history/prompts/task-crud/003-phase-i-architecture-spec.plan.prompt.md
tests:
  - null
---

## Prompt

Create architecture specification for Phase I console todo app.

File: @specs/architecture.md

Include:
- Folder structure
- Module breakdown
- src/
   main.py
   task_manager.py
   models.py
   cli.py

Design Principles:
- Single responsibility
- Modular code
- Easy future API migration
- AI generated implementation only

## Response snapshot

Created `specs/architecture.md` with the following sections:

- **Summary**: Three-layer (CLI → Service → Model), AI-generated, Phase II migration-ready
- **Technical Context**: Python 3.13, UV, stdlib-only, zero-dep, ASCII-safe output
- **Constitution Check**: All six gates verified PASS against real codebase
- **Folder Structure**: Full annotated tree (src/, tests/, specs/, history/, .specify/)
- **Module Breakdown** (per module):
  - `models.py` — `Task` dataclass + `TaskStore`; backing structure note; future DB swap path
  - `task_service.py` — Constructor-injected `TaskService`; return-value signalling; Phase II FastAPI path
  - `cli.py` — Module-level handler functions; `monkeypatch`-friendly; Phase II route handler mapping
  - `main.py` — Pure router; no logic; `KeyboardInterrupt` handling; `match` statement note
- **Component Interaction Diagram**: ASCII flow from stdin → main → cli → service → model → RAM
- **Import Direction**: Strict one-way chain enforced
- **Design Principles**: Single responsibility (change-reason table), modular isolation, API migration table, AI-only rule
- **Error Handling Architecture**: Three-tier diagram (CLI catches inputs, service returns None/False, top-level catches unexpected)
- **Testing Architecture**: Three test files, isolation rule, run command
- **Complexity Justification**: Three decisions documented with alternatives rejected

Note: User prompt referenced `task_manager.py`; actual module is `task_service.py` — documented in spec with a callout note.


## Outcome

- ✅ Impact: Complete architecture reference document grounded in actual source code; serves as authoritative blueprint for Phase I and migration guide for Phase II
- 🧪 Tests: No tests run (architecture is a document artifact); testing architecture defined in the spec
- 📁 Files: specs/architecture.md (created)
- 🔁 Next prompts: `/sp.tasks task-crud` to create testable task list, then implement test layer (`tests/`)
- 🧠 Reflection: Architecture grounded in real code reads (all four src files); no invented APIs — every method signature verified against live implementation

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): N/A — document artifact
- Prompt variant (if applicable): initial
- Next experiment: generate tasks.md from this architecture + the feature spec, then validate each task maps to a specific acceptance criterion
