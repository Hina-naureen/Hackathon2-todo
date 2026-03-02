# API Specification: Chat Endpoint — Phase III

**Version:** 1.1.0
**Date:** 2026-03-02
**Status:** Implemented
**Stage:** green
**Phase:** III
**Base URL:** `http://localhost:8000` (development)
**Overview:** `specs/overview.md`
**Auth spec:** `specs/features/authentication.md`
**REST tasks spec:** `specs/api/rest-endpoints.md`
**Constitution:** `.specify/memory/constitution.md`

---

## Overview

The `/api/chat` endpoint is the Phase III AI chat gateway. In Phase III stub
form the backend performs no external AI calls; it returns a deterministic
echo reply so the frontend can be developed and tested against a real HTTP
contract. An OpenAI (or equivalent) integration will replace the echo logic in
a later increment — the request/response schema will not change.

---

## Global Rules (inherited from `specs/api/rest-endpoints.md`)

| Rule | Detail |
|------|--------|
| Base path | `/api/` |
| Content type | `application/json` for request body and response |
| Auth header | `Authorization: Bearer <jwt>` required |
| User scoping | Replies are scoped to the authenticated user — `user_id` (from JWT `sub`) is available to the route for future personalisation |

---

## Endpoint

---

### `POST /api/chat`

Send a user message and receive an AI-generated (or stub) reply.

**Authentication:** Required

**Request body:**

```json
{
  "message": "What tasks do I have today?"
}
```

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `message` | string | **Yes** | Must be non-empty after stripping whitespace |

**Response `200 OK`:**

```json
{
  "reply": "You have 2 pending tasks: Buy milk, Submit report.",
  "trace_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "actions": [
    {
      "tool": "list_tasks",
      "args": { "filter": "pending" },
      "result": { "tasks": [...], "count": 2 }
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `reply` | string | The assistant's natural-language response (from OpenAI or local simulation). |
| `trace_id` | string | UUID v4 generated per request. Used for log correlation. |
| `actions` | array | Every tool invoked during this request. Empty (`[]`) when no tools were called. |

**`actions` item schema:**

| Field | Type | Description |
|-------|------|-------------|
| `tool` | string | Tool name, e.g. `"create_task"`, `"list_tasks"` |
| `args` | object | Arguments passed to the tool (user_id excluded) |
| `result` | any | Tool return value — task object, list, or `{"error": "..."}` |

**Error responses:**

| Condition | Status | Body |
|-----------|--------|------|
| Empty or whitespace-only message | `400` | `{"detail": "Message cannot be empty."}` |
| Missing auth | `401` | `{"detail": "Not authenticated."}` |
| Expired token | `401` | `{"detail": "Token expired."}` |
| Invalid token | `401` | `{"detail": "Invalid token."}` |
| Missing required field | `422` | FastAPI default validation error |

**Acceptance Criteria:**

1. Authenticated request with a non-empty `message` returns `200` with `reply`, `trace_id`, and `actions`.
2. `reply` is a non-empty string produced by the TaskAgent (OpenAI or local simulation fallback).
3. `trace_id` is a valid UUID v4 string, unique per request.
4. Empty or whitespace-only `message` returns `400`.
5. Request without `Authorization` header returns `401 {"detail": "Not authenticated."}`.
6. Request with an invalid JWT returns `401 {"detail": "Invalid token."}`.
7. `user_id` from the JWT `sub` claim is available to the handler but is **never** included in the response.
8. `actions` is a list; it is empty when the agent returns without calling any tools.
9. When any mutation tool runs, the frontend calls `onMutation()` to refresh the task list.
10. If the agent raises any exception, the route falls back to `"You said: <message>"` — HTTP 200, never 500.

---

## Schemas

### ChatRequest (request body)

```
{
  "message": string  (required, non-empty after strip)
}
```

### ChatResponse (response body)

```
{
  "reply":    string   (assistant reply text)
  "trace_id": string   (UUID v4, unique per request)
  "actions":  array    (list of ActionTraceOut — may be empty)
}
```

### ActionTraceOut (element of `actions`)

```
{
  "tool":   string   (tool name)
  "args":   object   (tool arguments passed by the LLM)
  "result": any      (tool return value or {"error": "..."})
}
```

---

## Error Taxonomy

Inherits the global taxonomy from `specs/api/rest-endpoints.md §Error Taxonomy`.
Additional entry specific to this endpoint:

| HTTP Status | Meaning | When Used |
|-------------|---------|-----------|
| `400 Bad Request` | Empty message | `message` is empty or whitespace-only after strip |

---

## Phase III — Production Behaviour

| Concern | With `OPENAI_API_KEY` | Without `OPENAI_API_KEY` |
|---------|----------------------|--------------------------|
| Reply source | OpenAI `gpt-4o-mini` + tool calling | Local keyword simulation (`_local_simulate`) |
| Tool calls | Real (creates/updates/deletes tasks) | None (no tool calls in simulation) |
| Latency | p95 < 5 s | Instant |
| Errors | 400, 401, 503 (openai pkg missing) | 400, 401 |
| Schema | `reply`, `trace_id`, `actions` | Same — always consistent |
| Streaming | Not supported | Not applicable |

The schema (`reply`, `trace_id`, `actions`) is identical regardless of whether
the OpenAI key is set. The frontend never needs to change.

---

## Implementation Notes

- Route file: `backend/src/routes/chat.py`
- Registered in `backend/src/app.py` at prefix `/api/chat` with tag `chat`
- Auth dependency: `src.auth.dependencies.get_current_user` (identical to tasks)
- No database interaction in stub phase
- `trace_id` generated with `uuid.uuid4()`

---

## References

| Document | Path |
|----------|------|
| Phase II REST spec | `specs/api/rest-endpoints.md` |
| Auth spec | `specs/features/authentication.md` |
| Overview | `specs/overview.md` |
| Global constitution | `.specify/memory/constitution.md` |
| Route implementation | `backend/src/routes/chat.py` |
| Tests | `backend/tests/test_chat.py` |
