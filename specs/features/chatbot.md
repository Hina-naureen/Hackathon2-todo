# Feature Specification: AI Chatbot — Phase III

**Version:** 1.0.0
**Date:** 2026-02-25
**Status:** Draft
**Stage:** spec
**Phase:** III
**References:**
- `specs/api/chat-endpoint.md` — HTTP contract
- `specs/api/mcp-tools.md` — tool definitions
- `specs/agents/agent-behavior.md` — agent loop rules
- `specs/api/rest-endpoints.md` — task CRUD contract (tools call this internally)
- `.specify/memory/constitution.md` — global rules

---

## Overview

Phase III adds an AI assistant that allows users to manage their todo list through
natural language conversation. The assistant runs as an agentic loop: it receives
a user message, decides which task operations to perform via tool calls, executes
them against the real database, and returns a natural-language reply.

No frontend changes are required for Phase III core. The existing ChatPanel
already renders the `reply` and surfaces the `actions` trace.

---

## User Stories

### US-CHAT-01 — Create a task via chat

> As an authenticated user, I want to type "Add a task to buy groceries" and have
> the assistant create that task in my list.

**Acceptance Criteria:**
1. The assistant calls the `create_task` tool with the correct title.
2. The task appears in the user's task list after the conversation.
3. The reply confirms the task was created and includes the task title.
4. The `actions` array in the response contains one entry with `tool: "create_task"`.

---

### US-CHAT-02 — List tasks via chat

> As an authenticated user, I want to ask "What tasks do I have?" and receive
> a readable summary of my current tasks.

**Acceptance Criteria:**
1. The assistant calls `list_tasks` with the appropriate filter.
2. The reply lists task titles (and optionally their IDs and statuses).
3. The `actions` array contains one entry with `tool: "list_tasks"`.
4. If the user has no tasks, the reply states that clearly.

---

### US-CHAT-03 — Complete a task via chat

> As an authenticated user, I want to say "Mark task 3 as done" and have the
> assistant toggle it.

**Acceptance Criteria:**
1. The assistant calls `toggle_complete` with the correct task ID.
2. The task's `completed` flag is set to `true` in the database.
3. The reply confirms which task was marked complete.
4. If the task ID does not exist, the reply states the task was not found.

---

### US-CHAT-04 — Update a task via chat

> As an authenticated user, I want to say "Rename task 2 to 'Buy organic milk'" and
> have the assistant update it.

**Acceptance Criteria:**
1. The assistant calls `update_task` with the correct ID and new title.
2. The task title is updated in the database.
3. The reply confirms the update.

---

### US-CHAT-05 — Off-topic redirect

> As a user, if I ask "What's the weather today?" the assistant politely
> redirects me to task-related actions.

**Acceptance Criteria:**
1. The assistant returns a reply that declines the off-topic request.
2. The reply suggests relevant task actions instead.
3. No tools are called; `actions` is empty.

---

### US-CHAT-06 — User isolation enforced

> As a user, I cannot access or modify another user's tasks through chat.

**Acceptance Criteria:**
1. All tool calls are scoped to the authenticated user's `user_id` (from JWT).
2. Attempting to operate on another user's task ID returns a not-found result
   (same as the REST API — no information leakage).

---

## Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-CHAT-001 | Agent only reads/writes task data via the four defined tools. |
| FR-CHAT-002 | `user_id` from the JWT `sub` claim is threaded through every tool call. |
| FR-CHAT-003 | A valid `OPENAI_API_KEY` must be set; without it the route returns `503`. |
| FR-CHAT-004 | The agent loop has a maximum iteration cap of 5 to prevent runaway calls. |
| FR-CHAT-005 | The response includes an `actions` array listing every tool invoked. |
| FR-CHAT-006 | Empty or whitespace-only messages return `400`. |
| FR-CHAT-007 | Missing/invalid JWT returns `401` (unchanged from Phase III stub). |
| FR-CHAT-008 | Tool errors (e.g., task not found) are surfaced in the `actions.result` and reflected in the reply; they do not raise HTTP 5xx. |

---

## Non-Functional Requirements

| Concern | Target |
|---------|--------|
| Latency | p95 < 5 s (subject to OpenAI upstream latency) |
| Model | `gpt-4o-mini` (cost-efficient, function-calling capable) |
| Max tool iterations | 5 per request |
| Key management | `OPENAI_API_KEY` env var; never hardcoded |

---

## Out of Scope (Phase III)

- Streaming responses (Server-Sent Events)
- Multi-turn conversation memory (each request is stateless)
- Task deletion via chat
- File uploads or attachments
- Rate limiting on the chat endpoint
- OpenAI cost tracking

---

## References

| Document | Path |
|----------|------|
| HTTP contract | `specs/api/chat-endpoint.md` |
| Tool definitions | `specs/api/mcp-tools.md` |
| Agent behavior | `specs/agents/agent-behavior.md` |
| Task REST spec | `specs/api/rest-endpoints.md` |
| Auth spec | `specs/features/authentication.md` |
| Route implementation | `backend/src/routes/chat.py` |
| Agent implementation | `backend/agents/agent.py` |
| Tool implementation | `backend/agents/tools.py` |
| Tests | `backend/tests/test_chat.py`, `backend/tests/test_agent.py` |
