# API Specification: Chat Endpoint — Phase III

**Version:** 1.0.0
**Date:** 2026-02-25
**Status:** Draft
**Stage:** spec
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
  "reply": "You said: What tasks do I have today?",
  "trace_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `reply` | string | The assistant's response. In Phase III stub: `"You said: <message>"`. |
| `trace_id` | string | UUID v4 generated per request. Enables log correlation when real AI calls are added. |

**Error responses:**

| Condition | Status | Body |
|-----------|--------|------|
| Empty or whitespace-only message | `400` | `{"detail": "Message cannot be empty."}` |
| Missing auth | `401` | `{"detail": "Not authenticated."}` |
| Expired token | `401` | `{"detail": "Token expired."}` |
| Invalid token | `401` | `{"detail": "Invalid token."}` |
| Missing required field | `422` | FastAPI default validation error |

**Acceptance Criteria:**

1. Authenticated request with a non-empty `message` returns `200` with `reply` and `trace_id`.
2. `reply` in Phase III stub is exactly `"You said: <stripped message>"`.
3. `trace_id` is a valid UUID v4 string, unique per request.
4. Empty or whitespace-only `message` returns `400`.
5. Request without `Authorization` header returns `401 {"detail": "Not authenticated."}`.
6. Request with an invalid JWT returns `401 {"detail": "Invalid token."}`.
7. `user_id` from the JWT `sub` claim is available to the handler (for future personalisation) but is **never** included in the response.

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
  "reply":    string  (assistant reply text)
  "trace_id": string  (UUID v4, unique per request)
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

## Phase III Stub vs Production

| Concern | Phase III Stub | Production (future) |
|---------|---------------|---------------------|
| Reply source | Deterministic echo: `"You said: <message>"` | OpenAI / LLM call |
| Latency | Instant | 500 ms – 5 s |
| Errors | 400, 401 only | + 502 (upstream AI failure), 429 (rate limit) |
| Context | None | Task list injected as system prompt |
| Streaming | Not supported | Optional (Server-Sent Events) |

The schema (`reply`, `trace_id`) is stable across stub and production. The
frontend does not need to change when the stub is replaced.

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
