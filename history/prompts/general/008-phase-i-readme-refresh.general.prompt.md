---
id: "008"
title: Phase I README Refresh
stage: general
date: 2026-02-24
surface: agent
model: claude-sonnet-4-6
feature: none
branch: master
user: pc
command: "Create Phase I README.md with setup, CLI usage, features, SDD workflow"
labels: ["readme","documentation","phase-1","sdd-workflow","setup","cli-usage"]
links:
  spec: specs/constitution.md
  ticket: null
  adr: null
  pr: null
files:
  - README.md
tests:
  - "uv run todo boots cleanly after write"
  - "uv run pytest tests/ -q — 107 passed"
---

## Prompt

Create Phase I README.md with:
- Setup instructions
- How to run CLI
- Features list
- Spec-driven workflow explanation

## Response snapshot

Full rewrite of README.md. Previous version had stale content from pre-refactor CLI (old
section headers `--- Add New Task ---`, old status icons `[DONE]`/`[    ]`, old menu
output). All updated to reflect current professional CLI layout.

Sections written:

1. **Project Overview** — SDD summary, 5-phase roadmap context
2. **Features** — table with # / feature / menu key / full behaviour description
3. **Requirements** — Python 3.13+, UV, no runtime deps, pytest for dev
4. **Setup** — UV install (Windows + macOS/Linux), git clone, uv sync
5. **Running the App** — `uv run todo` with actual current boxed menu output
6. **Usage Examples** — all 5 features with exact current CLI output:
   - Add: `>> Add New Task` header, aligned prompts, success message
   - View: `=` heavy border table, `[ ]`/`[x]` status icons, task count
   - Update: Enter-to-keep explained, success message
   - Delete: `y/n` confirmation flow
   - Toggle: complete/pending flip
7. **Running Tests** — `uv run pytest tests/ -v`, 107 tests, expected output
8. **Project Structure** — full annotated tree (src/, tests/, specs/, history/)
9. **Spec-Driven Development Workflow** — lifecycle table, rules list, document
   hierarchy with precedence order, layer import diagram
10. **Error Reference** — full error catalogue from spec
11. **Roadmap** — Phase I–V stack table
12. **Key Commands** — quick-reference block at the bottom

## Outcome

- ✅ Impact: README is fully synced with current CLI appearance; SDD workflow clearly
  explained with lifecycle table and rules; serves as the definitive Phase I reference
- 🧪 Tests: boot PASS, 107/107 pytest PASS after write
- 📁 Files: README.md (full rewrite, 208 lines)
- 🔁 Next prompts: Phase II planning — REST API with FastAPI + Neon DB
- 🧠 Reflection: Key fix was syncing all terminal output examples with the professional
  CLI refactor (boxed menu, `>> section` headers, `[ ]`/`[x]` icons, indented prompts)

## Evaluation notes (flywheel)

- Failure modes observed: stale CLI examples in previous README
- Graders run and results (PASS/FAIL): boot PASS, pytest 107/107 PASS
- Prompt variant (if applicable): refresh (previous version existed)
- Next experiment: add a CONTRIBUTING.md that explains how to add a new spec stage
