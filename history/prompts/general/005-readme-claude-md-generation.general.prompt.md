---
id: "005"
title: README and CLAUDE.md Generation
stage: general
date: 2026-02-24
surface: agent
model: claude-sonnet-4-6
feature: none
branch: master
user: pc
command: "Generate README.md and CLAUDE.md for Phase I project"
labels: ["readme","claude-md","documentation","phase-1","spec-reading","workflow","setup"]
links:
  spec: specs/constitution.md
  ticket: null
  adr: null
  pr: null
files:
  - README.md
  - CLAUDE.md
tests:
  - "smoke: uv run todo boots after file writes"
---

## Prompt

Generate:

README.md
CLAUDE.md

README.md must include:
- Setup steps
- Python version
- How to run console app
- Project overview

CLAUDE.md must include:
- How Claude Code should read specs
- Spec referencing rules
- Phase I workflow

## Response snapshot

### README.md (full rewrite — 241 lines)
- Project overview with phase roadmap
- Requirements table (Python 3.13+, UV, no dependencies)
- UV installation steps (Windows PowerShell + macOS/Linux curl)
- uv sync + uv run todo setup
- Full usage examples for all 5 features (add, view, toggle, delete update)
- Updated project structure tree (task_manager.py replacing old task_service.py)
- SDD workflow diagram with document hierarchy table
- Running tests section
- Roadmap table (Phase I–V)
- Development rules summary

### CLAUDE.md (appended — existing rules preserved + Phase I section added)

New section added at bottom: "Phase I — Spec Reading Protocol" covering:
- Session start checklist: read 4 spec files in order before any work
- Spec referencing rules: citation format, heading-path style, no line numbers
- Spec hierarchy and precedence order (constitution > architecture > feature spec > historical)
- "Spec wins over code" rule

New section: "Phase I — Development Workflow" covering:
- Full lifecycle table (Constitution → Spec → Architecture → Tasks → Red → Green → Refactor)
- Stage-to-command-to-output mapping table
- Phase I file map (which file to edit for each concern)
- Layer import direction rule (main → cli → task_manager → models)
- Pre-implementation checklist (4 questions Claude must answer before writing code)
- PHR stage reference table

## Outcome

- ✅ Impact: Both documents are the definitive project reference; CLAUDE.md now embeds spec-reading protocol that any new session must follow
- 🧪 Tests: uv run todo boots cleanly after both file writes
- 📁 Files: README.md (rewritten), CLAUDE.md (appended with Phase I sections)
- 🔁 Next prompts: Write test suite (test_models.py, test_task_manager.py, test_cli.py) using pytest
- 🧠 Reflection: Existing CLAUDE.md agent rules were preserved intact; Phase I sections added as a new named block to avoid collisions with Spec-Kit Plus tooling

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): smoke PASS — app boots after writes
- Prompt variant (if applicable): initial
- Next experiment: validate that CLAUDE.md session start checklist is followed in the next fresh session by asking Claude to narrate what it read at session start
