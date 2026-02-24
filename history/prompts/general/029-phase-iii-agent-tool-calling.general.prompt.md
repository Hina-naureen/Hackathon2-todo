---
id: "029"
title: "Phase III Agent Tool Calling Implementation"
stage: general
date: "2026-02-25"
surface: agent
model: claude-sonnet-4-6
feature: "none"
branch: master
user: Hina-naureen
command: "Upgrade /api/chat to use an AI Agent with tool calling"
labels: ["phase-iii", "agent", "tool-calling", "openai", "backend", "spec"]
links:
  spec: "specs/features/chatbot.md"
  ticket: "null"
  adr: "null"
  pr: "null"
files:
  - "specs/features/chatbot.md"
  - "specs/api/mcp-tools.md"
  - "specs/agents/agent-behavior.md"
  - "backend/agents/__init__.py"
  - "backend/agents/prompts.py"
  - "backend/agents/tools.py"
  - "backend/agents/agent.py"
  - "backend/src/routes/chat.py"
  - "backend/pyproject.toml"
  - "backend/tests/test_chat.py"
  - "backend/tests/test_agent.py"
tests:
  - "tests/test_agent.py (36 tests — tool functions + dispatch + agent loop)"
  - "tests/test_chat.py (11 tests — HTTP contract, actions trace, auth)"
  - "tests/test_api.py (37 tests — unchanged, no regressions)"
---

## Prompt

Upgrade /api/chat to use an AI Agent with tool calling.

Create specs: specs/features/chatbot.md, specs/api/mcp-tools.md, specs/agents/agent-behavior.md

Implement backend/agents/: agent.py, tools.py, prompts.py

Tools (MCP-style) must call existing task CRUD endpoints internally:
create_task, list_tasks, update_task, toggle_complete

Rules:
- Agent must only modify data via tools
- JWT user context must be enforced
- If user asks non-todo question, politely redirect

Update /api/chat to return assistant reply and also include "actions" trace.

Add tests for tool calling with mocked agent responses (no real OpenAI key required yet).

## Response

### Spec files (3 new)

**specs/features/chatbot.md** — 6 user stories (US-CHAT-01 through 06) with
acceptance criteria, functional requirements table, and NFR targets.

**specs/api/mcp-tools.md** — Full contract for each tool function: parameters,
success/error result shapes, business rules, security constraints.

**specs/agents/agent-behavior.md** — Agentic loop diagram, LLM interface spec
(_call_llm), LLMMessage/LLMToolCall/ActionTrace type definitions, system prompt
rules, safety constraints, error handling table.

### backend/agents/ package (new)

**agents/prompts.py** — `SYSTEM_PROMPT` with 7 rules: tool-only data access,
mandatory tool use, off-topic redirect, confirmation replies, multi-tool
sequencing, error communication.

**agents/tools.py** — Four tool functions (`create_task`, `list_tasks`,
`update_task`, `toggle_complete`) that call `TaskManager` + `DBTaskStore`
directly (in-process, no HTTP). Each returns a plain dict; errors are returned
as `{"error": "..."}` rather than raised. `call_tool()` dispatch function.
`TOOL_SCHEMAS` list for OpenAI function calling.

**agents/agent.py** — `LLMMessage`, `LLMToolCall`, `ActionTrace` dataclasses.
`TaskAgent.run()` agentic loop (max 5 iterations). `TaskAgent._call_llm()` is
the only OpenAI touch-point; it raises HTTP 503 if `OPENAI_API_KEY` is unset or
`openai` is not installed. Monkeypatching `_call_llm` on agent instances or at
the class level enables all tests to run without a real API key.

### backend/src/routes/chat.py (updated)

- Added `Session = Depends(get_session)` to inject DB session into the route
- Added `ActionTraceOut` Pydantic model (`tool`, `args`, `result`)
- Extended `ChatResponse` with `actions: list[ActionTraceOut]`
- Route body: instantiates `TaskAgent(session, user_id)`, calls `agent.run(message)`,
  maps `ActionTrace` dataclasses to `ActionTraceOut` Pydantic models
- Echo stub removed; agent handles all replies

### backend/pyproject.toml (updated)

- Added `openai>=1.0.0` (resolved to `openai==2.24.0`)
- Added `"agents"` to `[tool.hatch.build.targets.wheel] packages`

### backend/tests/test_chat.py (updated)

- Replaced echo-specific tests with response-structure tests
- Added `session` fixture (chat route now uses DB)
- `client` fixture monkeypatches `TaskAgent._call_llm` at class level
- Added `TestChatActions.test_action_trace_fields_present`: monkeypatches a
  single create_task tool call, verifies the action appears in the HTTP response

### backend/tests/test_agent.py (new, 36 tests)

Four test classes for tool functions + dispatch, one for the agent loop:
- `TestCreateTaskTool` (8 tests): happy path, validation errors, strip
- `TestListTasksTool` (5 tests): all/pending/completed filters, user isolation
- `TestUpdateTaskTool` (6 tests): title/desc update, null keeps existing, errors
- `TestToggleCompleteTool` (4 tests): pending/completed toggle, errors
- `TestCallToolDispatch` (3 tests): unknown tool, dispatch, user_id injection
- `TestAgentLoop` (10 tests): no-tool reply, each tool type, multi-tool
  sequence, error in-band, safety fallback, off-topic redirect, user isolation

## Outcome

- [x] 3 spec files written (chatbot.md, mcp-tools.md, agent-behavior.md)
- [x] agents/ package: prompts.py, tools.py, agent.py, __init__.py
- [x] Agent only modifies data via tools (no direct ORM calls)
- [x] JWT user_id injected into every tool call
- [x] Off-topic redirect tested (test_off_topic_returns_reply_with_empty_actions)
- [x] ChatResponse extended with actions: list[ActionTraceOut]
- [x] 47/47 new tests pass (36 agent + 11 chat)
- [x] 191/191 total tests pass (zero regressions)
- [x] No real OPENAI_API_KEY required for any test
- [x] openai==2.24.0 installed
