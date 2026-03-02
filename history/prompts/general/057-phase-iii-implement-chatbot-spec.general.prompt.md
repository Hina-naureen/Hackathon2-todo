---
id: "057"
title: Implement chatbot spec — due_date end-to-end
stage: green
date: 2026-03-02
surface: agent
model: claude-sonnet-4-6
feature: chatbot
branch: master
user: pc
command: Implement @specs/features/chatbot.md
labels: ["phase-iii","chatbot","due-date","implementation","green"]
links:
  spec: specs/features/chatbot.md
  ticket: null
  adr: null
  pr: null
files:
  - backend/src/db_models.py
  - backend/alembic/versions/002_add_due_date.py
  - backend/agents/tools.py
  - backend/agents/prompts.py
  - backend/agents/agent.py
  - backend/src/routes/chat.py
  - backend/src/routes/tasks.py
  - frontend/components/ChatPanel.tsx
  - run_tests.bat (temp — can be deleted)
tests:
  - backend/tests/test_agent.py (syntax verified)
  - backend/tests/test_chat.py (syntax verified)
---

## Prompt

Implement @specs/features/chatbot.md

## Response snapshot

All spec requirements implemented and syntax-verified. Key changes:

1. `db_models.py` — `due_date: Optional[datetime]` on Task + TaskCreate + TaskUpdate + TaskRead
2. `alembic/versions/002_add_due_date.py` — ADD COLUMN due_date TIMESTAMP NULL (revises 001)
3. `agents/tools.py` — create_task/update_task accept due_date param; _parse_due_date() helper; list_tasks returns due_date; TOOL_SCHEMAS updated
4. `agents/prompts.py` — 4 due_date rules with ISO 8601 examples
5. `agents/agent.py` — run(today=) injects [Today is YYYY-MM-DD] context note
6. `routes/chat.py` — ChatRequest.today optional field; passed to agent.run()
7. `routes/tasks.py` — POST/PUT handlers now write due_date from request body
8. `ChatPanel.tsx` — sends today: new Date().toISOString().split('T')[0]

All 6 core Python files pass ast.parse() syntax check.
Git Bash cannot run .exe from Windows venv — tests must be run from cmd/PowerShell.

## Outcome

- ✅ Impact: chatbot spec fully implemented including due_date (US-CHAT-08/09, FR-CHAT-011/012)
- 🧪 Tests: syntax OK; to run: `cd backend && uv run pytest tests\test_agent.py tests\test_chat.py -v` (from cmd.exe)
- 📁 Files: 8 files modified
- 🔁 Next prompts: run alembic migration; run test suite from cmd.exe; test end-to-end with OPENAI_API_KEY
- 🧠 Reflection: Git Bash on Windows cannot execute Windows venv .exe files; always use cmd/PowerShell for uv run commands

## Evaluation notes (flywheel)

- Failure modes observed: REST routes (tasks.py) were not updated to handle due_date from body — caught in static review and fixed
- Graders run and results (PASS/FAIL): ast.parse syntax check — PASS (6/6 files)
- Prompt variant (if applicable): direct spec implementation command
- Next experiment: run full pytest suite from cmd.exe to confirm all 43+ tests pass
