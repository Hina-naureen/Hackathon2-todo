# API Specification: MCP-Style Agent Tools — Phase III

**Version:** 1.2.0
**Date:** 2026-03-02
**Status:** Implemented
**Stage:** green
**Phase:** III
**References:**
- `specs/features/chatbot.md` — feature context
- `specs/api/rest-endpoints.md` — underlying REST contracts these tools mirror
- `specs/agents/agent-behavior.md` — how the agent invokes these tools

---

## Overview

The agent tools are implemented as plain Python functions in `backend/agents/tools.py`.
They are *not* HTTP endpoints — they call `TaskManager` and `DBTaskStore` directly
(in-process), using the same validated `user_id` and `Session` that the REST routes
use. This avoids an HTTP round-trip while preserving identical business logic and
user-scoping guarantees.

Each tool function returns a plain `dict`. The dict is serialized to JSON and
included in the LLM's tool-result message for context, and also surfaced in the
HTTP response's `actions` array for observability.

---

## Tool Definitions

---

### `create_task`

Create a new task for the authenticated user.

**Parameters:**

| Name | Type | Required | Constraints |
|------|------|----------|-------------|
| `title` | string | **Yes** | 1–200 chars after strip; non-empty |
| `description` | string | No | 0–500 chars; defaults to `""` |
| `due_date` | string \| null | No | ISO 8601 datetime string (`"2026-03-03T14:00:00"`); `null` = no due date |

**Success result:**

```json
{
  "id": 5,
  "title": "Meeting",
  "description": "",
  "completed": false,
  "due_date": "2026-03-03T14:00:00"
}
```

**Error result (returned in dict, not as exception):**

```json
{ "error": "Title cannot be empty." }
```

**Business rules:**
- Title is stripped of leading/trailing whitespace before storage.
- `due_date` is stored as a naive UTC datetime; the agent converts natural-language
  temporal expressions to ISO 8601 before calling this tool.
- Mirrors `POST /api/tasks` validation exactly.

---

### `list_tasks`

Return all tasks for the authenticated user, optionally filtered by status.

**Parameters:**

| Name | Type | Required | Allowed values |
|------|------|----------|----------------|
| `filter` | string | No | `"all"` (default), `"pending"`, `"completed"` |

**Success result:**

```json
{
  "tasks": [
    { "id": 1, "title": "Buy groceries", "description": "", "completed": false },
    { "id": 2, "title": "Submit report", "description": "", "completed": true }
  ],
  "count": 2
}
```

**Business rules:**
- Tasks are always ordered by ascending `id`.
- `"pending"` filters to `completed == false`; `"completed"` filters to `completed == true`.
- Never exposes tasks belonging to other users.

---

### `update_task`

Update the title and/or description of an existing task.

**Parameters:**

| Name | Type | Required | Semantics |
|------|------|----------|-----------|
| `id` | integer | **Yes** | Task ID to update |
| `title` | string \| null | No | `null` = keep current; non-empty string = replace |
| `description` | string \| null | No | `null` = keep current; any string (including `""`) = replace |
| `due_date` | string \| null | No | ISO 8601 string = set new due date; `null` = keep current; `""` = clear due date |

**Success result:**

```json
{
  "id": 1,
  "title": "Buy organic milk",
  "description": "From the farmers market",
  "completed": false
}
```

**Error result:**

```json
{ "error": "Task #99 not found." }
```

**Business rules:**
- Mirrors `PUT /api/tasks/{id}` validation (title 1–200 chars, desc 0–500 chars).
- `updated_at` is refreshed on every successful update.
- Only the authenticated user's tasks can be updated.

---

### `delete_task`

Permanently delete a task owned by the authenticated user.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `id` | integer | **Yes** | Task ID to delete |

**Success result:**

```json
{
  "deleted": true,
  "id": 3,
  "title": "Buy groceries"
}
```

**Error result:**

```json
{ "error": "Task #99 not found." }
```

**Business rules:**
- The task must belong to the authenticated user; cross-user deletes return a not-found error.
- The operation is permanent — there is no soft-delete or undo.
- Mirrors `DELETE /api/tasks/{id}` semantics exactly.

---

### `toggle_complete`

Toggle a task's `completed` flag between `true` and `false`.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `id` | integer | **Yes** | Task ID to toggle |

**Success result:**

```json
{
  "id": 2,
  "title": "Submit report",
  "completed": true
}
```

**Error result:**

```json
{ "error": "Task #99 not found." }
```

**Business rules:**
- Mirrors `PATCH /api/tasks/{id}/toggle`.
- `updated_at` is refreshed on every successful toggle.
- Only the authenticated user's tasks can be toggled.

---

## OpenAI Tool Schema

Each tool is registered as an OpenAI function-calling schema in `TOOL_SCHEMAS`
inside `backend/agents/tools.py`. The schemas are passed verbatim to
`openai.chat.completions.create(tools=TOOL_SCHEMAS)`.

The four schemas follow the JSON Schema subset supported by OpenAI function
calling (type: object, properties, required array).

---

## Tool Dispatch

`call_tool(session, user_id, tool_name, args)` in `agents/tools.py` is the
single dispatch point. It looks up `tool_name` in `TOOL_REGISTRY` and calls the
function with `(session, user_id, **args)`. Unknown tool names return:

```json
{ "error": "Unknown tool: <name>" }
```

The agent never calls tool functions directly — it always goes through
`call_tool`. This keeps the dispatch logic in one place and makes the agent
unit-testable.

---

## Security Constraints

| Constraint | Enforcement |
|------------|-------------|
| User scoping | `user_id` is injected from the JWT `sub` claim and passed to every tool call — never taken from the request body or LLM output |
| Data mutation via tools only | The agent's `run()` method only writes data by invoking `call_tool`; it never calls ORM methods directly |
| Validation parity | Each tool replicates the same validation rules as the corresponding REST endpoint |

---

## References

| Document | Path |
|----------|------|
| Feature spec | `specs/features/chatbot.md` |
| Agent behavior | `specs/agents/agent-behavior.md` |
| Task REST spec | `specs/api/rest-endpoints.md` |
| Tool implementation | `backend/agents/tools.py` |
| Agent implementation | `backend/agents/agent.py` |
