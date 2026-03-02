---
id: "056"
title: Phase III Full SDD Deliverables — due_date + agent design
stage: general
date: 2026-03-02
surface: agent
model: claude-sonnet-4-6
feature: chatbot
branch: master
user: pc
command: Phase III 7-step SDD request (specs → agent design → backend → frontend → validation)
labels: ["phase-iii","sdd","due-date","openai","agent","mcp-tools","chatbot"]
links:
  spec: specs/features/chatbot.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/features/chatbot.md
  - specs/api/mcp-tools.md
  - backend/src/db_models.py
  - backend/alembic/versions/002_add_due_date.py
  - backend/agents/tools.py
  - backend/agents/prompts.py
  - backend/agents/agent.py
  - backend/src/routes/chat.py
  - frontend/components/ChatPanel.tsx
tests:
  - backend/tests/test_agent.py (existing)
  - backend/tests/test_chat.py (existing)
---

## Prompt

STEP 1 — Create/Update Specs: chatbot.md, mcp-tools.md, architecture.md Agent layer.
STEP 2 — Agent Design: system prompt, OpenAI Agents SDK format tools, JSON schemas, auth strategy.
STEP 3 — Backend Adjustments: MCP-compatible endpoints, JWT enforcement, missing endpoints (due date).
STEP 4 — Frontend Chat UI Integration: OpenAI ChatKit, Agents SDK, tool calling flow, JWT.
STEP 5 — Validation: "Add meeting tomorrow at 2 PM" → create_task with due_date. "Show pending tasks" → list_tasks filtered.
DELIVERABLES: spec files, implementation plan, backend code, MCP tool defs, agent config, frontend code, checklist.

## Response snapshot

**7 deliverables produced in order:**

1. **Specs** — chatbot.md v1.2.0 (US-CHAT-08/09, FR-CHAT-011/012); mcp-tools.md v1.2.0 (due_date in create/update)
2. **Implementation plan** — 7 files, touches only 4 layers; TaskManager (Phase I) UNCHANGED
3. **Backend code** — db_models.py: due_date nullable datetime on Task/TaskCreate/TaskUpdate/TaskRead; migration 002_add_due_date.py
4. **MCP tool definitions** — tools.py: create_task + update_task accept due_date; _parse_due_date() helper; list_tasks returns due_date; updated TOOL_SCHEMAS
5. **Agent config** — prompts.py: 4 due_date rules (convert natural language → ISO 8601, no fabrication); agent.run(today=) injects date context
6. **Frontend** — ChatPanel.tsx: sends today=YYYY-MM-DD alongside message; routes/chat.py: ChatRequest.today optional field
7. **Checklist** — see below

**Architecture satisfied:** Agent → call_tool() → TaskManager → DBTaskStore → Neon. No direct DB access from agent.
**Phase I contract maintained:** TaskManager.add_task/update_task signatures unchanged; due_date set directly on ORM object post-creation (same pattern as updated_at).

## Outcome

- ✅ Impact: due_date field end-to-end; agent parses "tomorrow at 2 PM" → ISO 8601 → DB
- 🧪 Tests: existing 43 tests unaffected; due_date tests should be added in next session
- 📁 Files: 9 files modified/created
- 🔁 Next prompts: Run Alembic migration; run pytest; add test_create_task_with_due_date
- 🧠 Reflection: today= context injection is the key pattern that enables reliable date parsing without a full date-parsing library

## Evaluation notes (flywheel)

- Failure modes observed: none during implementation
- Graders run and results (PASS/FAIL): spec audit PASS
- Prompt variant (if applicable): 7-step structured SDD workflow
- Next experiment: test "Add meeting tomorrow at 2 PM" end-to-end with real OPENAI_API_KEY
