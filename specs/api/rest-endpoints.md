# API Specification: REST Endpoints — Phase II

**Version:** 1.0.0
**Date:** 2026-02-24
**Status:** Draft
**Stage:** spec
**Phase:** II
**Base URL:** `http://localhost:8000` (development)
**Overview:** `specs/overview.md`
**Auth spec:** `specs/features/authentication.md`
**DB schema:** `specs/database/schema.md`
**Constitution:** `.specify/memory/constitution.md`

---

## Overview

The FastAPI backend exposes a RESTful JSON API for task management. All task
endpoints require a valid Better Auth JWT in the `Authorization: Bearer` header.
The Phase I `TaskManager` class is reused unchanged; only the transport layer
(route handlers) and storage layer (SQLModel + Neon DB `TaskStore` adapter) are
new.

---

## Global Rules

| Rule | Detail |
|------|--------|
| Base path | `/api/` |
| Content type | `application/json` for all request bodies and responses |
| Auth header | `Authorization: Bearer <jwt>` required on all `/api/tasks` routes |
| User scoping | All task operations are scoped to the authenticated user — a user can never read or modify another user's tasks |
| ID type | Integer — auto-incremented by the database |
| Empty string vs null | A `null` field in `PUT /api/tasks/{id}` means "keep existing value"; an empty string is a validation error for `title` |
| Timestamps | All task responses include `created_at` and `updated_at` in ISO 8601 UTC format |

---

## Endpoints

---

### `GET /api/tasks`

Return all tasks belonging to the authenticated user, ordered by ascending `id`.

**Authentication:** Required

**Request:** No body.

**Response `200 OK`:**

```json
[
  {
    "id": 1,
    "title": "Buy groceries",
    "description": "Milk and eggs",
    "completed": false,
    "created_at": "2026-02-24T10:00:00Z",
    "updated_at": "2026-02-24T10:00:00Z"
  },
  {
    "id": 2,
    "title": "Submit report",
    "description": "",
    "completed": true,
    "created_at": "2026-02-24T11:00:00Z",
    "updated_at": "2026-02-24T12:30:00Z"
  }
]
```

Returns `[]` (empty array) when the user has no tasks. Never returns `404`.

**Acceptance Criteria:**

1. Authenticated request returns only the calling user's tasks.
2. Tasks are ordered by `id` ascending.
3. Empty task list returns `200` with `[]`.
4. Unauthenticated request returns `401`.
5. Tasks belonging to other users are never included.

---

### `POST /api/tasks`

Create a new task for the authenticated user.

**Authentication:** Required

**Request body:**

```json
{
  "title": "Prepare demo slides",
  "description": "Hackathon II presentation"
}
```

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `title` | string | **Yes** | 1–200 characters; whitespace-only is rejected |
| `description` | string | No | 0–500 characters; defaults to `""` if omitted |

**Response `201 Created`:**

```json
{
  "id": 3,
  "title": "Prepare demo slides",
  "description": "Hackathon II presentation",
  "completed": false,
  "created_at": "2026-02-24T14:00:00Z",
  "updated_at": "2026-02-24T14:00:00Z"
}
```

**Error responses:**

| Condition | Status | Body |
|-----------|--------|------|
| Empty title | `400` | `{"detail": "Title cannot be empty."}` |
| Whitespace-only title | `400` | `{"detail": "Title cannot be empty."}` |
| Title > 200 chars | `400` | `{"detail": "Title must be 200 characters or fewer."}` |
| Description > 500 chars | `400` | `{"detail": "Description must be 500 characters or fewer."}` |
| Missing auth | `401` | `{"detail": "Not authenticated."}` |

**Acceptance Criteria:**

1. Valid request creates a task and returns `201` with the full task object.
2. Returned `id` is a positive integer unique to this user's tasks.
3. `completed` is always `false` on creation.
4. Title is stored after stripping leading/trailing whitespace.
5. Omitting `description` stores `""`.
6. Empty `title` returns `400`.
7. `title` exceeding 200 characters returns `400`.
8. `description` exceeding 500 characters returns `400`.

---

### `GET /api/tasks/{id}`

Retrieve a single task by ID.

**Authentication:** Required

**Path parameter:** `id` — integer

**Response `200 OK`:**

```json
{
  "id": 1,
  "title": "Buy groceries",
  "description": "Milk and eggs",
  "completed": false,
  "created_at": "2026-02-24T10:00:00Z",
  "updated_at": "2026-02-24T10:00:00Z"
}
```

**Error responses:**

| Condition | Status | Body |
|-----------|--------|------|
| ID not found (or belongs to other user) | `404` | `{"detail": "Task #<id> not found."}` |
| Non-integer `id` in path | `422` | FastAPI default validation error |
| Missing auth | `401` | `{"detail": "Not authenticated."}` |

**Acceptance Criteria:**

1. Returns the task if it exists and belongs to the authenticated user.
2. Returns `404` if the task does not exist.
3. Returns `404` (not `403`) if the task belongs to a different user — no information leakage.

---

### `PUT /api/tasks/{id}`

Update a task's title and/or description.

`null` means "keep the existing value." An empty string for `title` is rejected.

**Authentication:** Required

**Path parameter:** `id` — integer

**Request body:**

```json
{
  "title": "Record demo video",
  "description": null
}
```

| Field | Type | Semantics |
|-------|------|-----------|
| `title` | `string \| null` | `null` → keep current; non-empty string → replace |
| `description` | `string \| null` | `null` → keep current; any string (including `""`) → replace |

**Response `200 OK`:** Full updated task object (same schema as `GET /api/tasks/{id}`).

**Error responses:**

| Condition | Status | Body |
|-----------|--------|------|
| Task not found | `404` | `{"detail": "Task #<id> not found."}` |
| Empty string `title` (not `null`) | `400` | `{"detail": "Title cannot be empty."}` |
| `title` > 200 chars | `400` | `{"detail": "Title must be 200 characters or fewer."}` |
| `description` > 500 chars | `400` | `{"detail": "Description must be 500 characters or fewer."}` |
| Missing auth | `401` | `{"detail": "Not authenticated."}` |

**Acceptance Criteria:**

1. `null` fields are preserved from the existing task — no overwrite.
2. Non-null fields are validated and updated.
3. `updated_at` is refreshed on every successful update.
4. Only the authenticated user's task can be updated.
5. An empty string `""` for `title` returns `400` (not the same as `null`).

---

### `DELETE /api/tasks/{id}`

Permanently delete a task. No confirmation round-trip in the REST API — the UI
layer handles the confirmation prompt.

**Authentication:** Required

**Path parameter:** `id` — integer

**Response `200 OK`:**

```json
{
  "detail": "Task #1 deleted."
}
```

**Error responses:**

| Condition | Status | Body |
|-----------|--------|------|
| Task not found | `404` | `{"detail": "Task #<id> not found."}` |
| Missing auth | `401` | `{"detail": "Not authenticated."}` |

**Acceptance Criteria:**

1. Successful delete removes the task from the database and returns `200`.
2. Subsequent `GET /api/tasks/{id}` for the deleted ID returns `404`.
3. The deleted task's ID is never reused in the same user's task list.
4. Only the authenticated user's task can be deleted.

---

### `PATCH /api/tasks/{id}/toggle`

Toggle a task's `completed` status between `true` and `false`.

**Authentication:** Required

**Path parameter:** `id` — integer

**Request:** No body.

**Response `200 OK`:** Full updated task object with the new `completed` value.

```json
{
  "id": 2,
  "title": "Submit report",
  "description": "",
  "completed": true,
  "created_at": "2026-02-24T11:00:00Z",
  "updated_at": "2026-02-24T13:00:00Z"
}
```

**Error responses:**

| Condition | Status | Body |
|-----------|--------|------|
| Task not found | `404` | `{"detail": "Task #<id> not found."}` |
| Missing auth | `401` | `{"detail": "Not authenticated."}` |

**Acceptance Criteria:**

1. A pending task (`completed: false`) becomes complete (`completed: true`).
2. A complete task (`completed: true`) becomes pending (`completed: false`).
3. `updated_at` is refreshed on every toggle.
4. Calling toggle twice restores the original state.
5. Only the authenticated user's task can be toggled.

---

## Error Taxonomy

| HTTP Status | Meaning | When Used |
|-------------|---------|-----------|
| `200 OK` | Success with body | GET, PUT, PATCH, DELETE |
| `201 Created` | Resource created | POST /api/tasks |
| `400 Bad Request` | Business validation failure | Empty title, length exceeded |
| `401 Unauthorized` | Missing or invalid JWT | All protected endpoints |
| `404 Not Found` | Resource not found | Task ID missing or belongs to other user |
| `422 Unprocessable Entity` | Request schema validation failure | Wrong field types, missing required fields |
| `500 Internal Server Error` | Unexpected server error | DB connection failure, unhandled exception |

---

## Shared Schemas

### TaskRead (response schema for all task endpoints)

```
{
  "id":          integer (positive, auto-incremented)
  "title":       string (1–200 chars)
  "description": string (0–500 chars)
  "completed":   boolean
  "created_at":  string (ISO 8601 UTC)
  "updated_at":  string (ISO 8601 UTC)
}
```

`user_id` is **never** included in any response.

### TaskCreate (request body for POST)

```
{
  "title":       string (required, 1–200 chars)
  "description": string (optional, 0–500 chars, default "")
}
```

### TaskUpdate (request body for PUT)

```
{
  "title":       string | null  (null = keep existing)
  "description": string | null  (null = keep existing)
}
```

Both fields are optional. An empty object `{}` is valid and results in no
changes (idempotent).

---

## CORS Configuration

| Setting | Value |
|---------|-------|
| Allowed origins (dev) | `http://localhost:3000` |
| Allowed origins (prod) | `ALLOWED_ORIGINS` env var |
| Allowed methods | `GET, POST, PUT, DELETE, PATCH, OPTIONS` |
| Allowed headers | `Authorization, Content-Type` |
| Allow credentials | `true` |

---

## API Versioning

Phase II does not version the API (YAGNI). The path prefix `/api/` provides
a namespace. If versioning is needed in Phase III, it will be `/api/v2/`.

---

## OpenAPI / Docs

FastAPI auto-generates OpenAPI documentation:

| URL | Purpose |
|-----|---------|
| `http://localhost:8000/docs` | Swagger UI (interactive testing) |
| `http://localhost:8000/redoc` | ReDoc (readable reference) |
| `http://localhost:8000/openapi.json` | Raw OpenAPI 3.1 schema |

---

## Phase I Mapping

| Phase I CLI action | Phase II REST equivalent |
|-------------------|--------------------------|
| Menu `1` — Add Task | `POST /api/tasks` |
| Menu `2` — View All | `GET /api/tasks` |
| Menu `3` — Update | `PUT /api/tasks/{id}` |
| Menu `4` — Delete | `DELETE /api/tasks/{id}` |
| Menu `5` — Toggle | `PATCH /api/tasks/{id}/toggle` |

The same `TaskManager` methods are called in both phases:

| Phase I call | Phase II call |
|--------------|--------------|
| `manager.add_task(title, desc)` | same |
| `manager.get_all_tasks()` | same |
| `manager.update_task(id, title, desc)` | same |
| `manager.delete_task(id)` | same |
| `manager.toggle_complete(id)` | same |

---

## References

| Document | Path |
|----------|------|
| Phase II overview | `specs/overview.md` |
| Auth spec | `specs/features/authentication.md` |
| Database schema | `specs/database/schema.md` |
| UI pages | `specs/ui/pages.md` |
| Phase I feature spec | `specs/features/task-crud.md` |
| Global constitution | `.specify/memory/constitution.md` |
