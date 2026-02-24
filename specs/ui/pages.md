# UI Specification: Pages — Phase II

**Version:** 1.0.0
**Date:** 2026-02-24
**Status:** Draft
**Stage:** spec
**Phase:** II
**Framework:** Next.js 16 (App Router) + TypeScript
**Auth:** Better Auth
**Overview:** `specs/overview.md`
**Auth spec:** `specs/features/authentication.md`
**API spec:** `specs/api/rest-endpoints.md`
**Constitution:** `.specify/memory/constitution.md`

---

## Overview

The frontend is a **Next.js 16 App Router** TypeScript application. It provides
three user-facing pages: sign-in, sign-up, and the protected tasks page. All
task data is fetched from the FastAPI backend with the user's Bearer token
attached. State is managed with React's built-in `useState` / `useEffect` — no
external state management library in Phase II (YAGNI).

---

## App Router Structure

```
frontend/
└── app/
    ├── layout.tsx                    # Root layout — font, global CSS, providers
    ├── page.tsx                      # / — redirect to /sign-in or /tasks
    ├── (auth)/                       # Route group — no shared layout for auth pages
    │   ├── sign-in/
    │   │   └── page.tsx              # Sign-in form
    │   └── sign-up/
    │       └── page.tsx              # Sign-up form
    ├── (protected)/                  # Route group — shared layout with header
    │   └── tasks/
    │       └── page.tsx              # Task list + CRUD
    └── api/
        └── auth/
            └── [...all]/
                └── route.ts          # Better Auth handler (all /api/auth/* routes)
```

---

## Middleware

**File:** `frontend/middleware.ts`

Runs on every request. Checks for a valid Better Auth session.

| Route pattern | Behaviour |
|---------------|-----------|
| `/tasks` (and sub-paths) | Redirect to `/sign-in` if no session |
| `/sign-in`, `/sign-up` | Redirect to `/tasks` if session already exists |
| `/` | Redirect to `/sign-in` (always) |
| `/api/*` | Pass through (no middleware check needed) |

---

## Pages

---

### Page 1 — Root `/`

**File:** `app/page.tsx`
**Auth:** None required
**Purpose:** Entry point redirect — users never see this page's content.

**Behaviour:**

- Server component.
- Checks for an active Better Auth session server-side.
- Session present → redirect to `/tasks`.
- No session → redirect to `/sign-in`.

---

### Page 2 — Sign In `/sign-in`

**File:** `app/(auth)/sign-in/page.tsx`
**Auth:** Must NOT be authenticated (middleware redirects to `/tasks` if already signed in)
**Purpose:** Allow a returning user to authenticate.

#### Layout

```
+-----------------------------------------------+
|                                               |
|           Evolution of Todo                   |
|                                               |
|   +---------------------------------------+   |
|   |  Sign In                              |   |
|   |                                       |   |
|   |  Email                                |   |
|   |  [________________________]           |   |
|   |                                       |   |
|   |  Password                             |   |
|   |  [________________________]           |   |
|   |                                       |   |
|   |  [  Sign In  ]                        |   |
|   |                                       |   |
|   |  Don't have an account? Sign up →     |   |
|   +---------------------------------------+   |
|                                               |
+-----------------------------------------------+
```

#### Fields

| Field | Type | Validation |
|-------|------|------------|
| Email | `<input type="email">` | Required; valid email format |
| Password | `<input type="password">` | Required; min 8 chars |

#### Behaviour

1. Form submits to Better Auth `signIn.email({ email, password })`.
2. On success → redirect to `/tasks`.
3. On failure → display `"Invalid email or password."` below the form (not per-field).
4. Show inline validation errors for empty/invalid fields before submitting.
5. Submit button shows a loading state while the sign-in request is in flight.
6. Submit button is disabled during loading.

#### Acceptance Criteria

1. Empty email shows `"Email is required."` inline.
2. Invalid email format shows `"Please enter a valid email address."` inline.
3. Empty password shows `"Password is required."` inline.
4. Correct credentials → redirect to `/tasks`.
5. Wrong credentials → `"Invalid email or password."` form-level error; no redirect.
6. Already authenticated user → redirect to `/tasks` (via middleware).
7. "Sign up →" link navigates to `/sign-up`.

---

### Page 3 — Sign Up `/sign-up`

**File:** `app/(auth)/sign-up/page.tsx`
**Auth:** Must NOT be authenticated (middleware redirects to `/tasks` if already signed in)
**Purpose:** Allow a new user to create an account.

#### Layout

```
+-----------------------------------------------+
|                                               |
|           Evolution of Todo                   |
|                                               |
|   +---------------------------------------+   |
|   |  Create Account                       |   |
|   |                                       |   |
|   |  Name                                 |   |
|   |  [________________________]           |   |
|   |                                       |   |
|   |  Email                                |   |
|   |  [________________________]           |   |
|   |                                       |   |
|   |  Password                             |   |
|   |  [________________________]           |   |
|   |  At least 8 characters                |   |
|   |                                       |   |
|   |  [  Create Account  ]                 |   |
|   |                                       |   |
|   |  Already have an account? Sign in →   |   |
|   +---------------------------------------+   |
|                                               |
+-----------------------------------------------+
```

#### Fields

| Field | Type | Validation |
|-------|------|------------|
| Name | `<input type="text">` | Required; min 1 char |
| Email | `<input type="email">` | Required; valid email format |
| Password | `<input type="password">` | Required; min 8 characters |

#### Behaviour

1. Form submits to Better Auth `signUp.email({ name, email, password })`.
2. On success → session established → redirect to `/tasks`.
3. On duplicate email → display `"An account with this email already exists."` form-level.
4. Show inline validation errors before submitting.
5. Submit button shows loading state during request.
6. Submit button is disabled during loading.

#### Acceptance Criteria

1. Empty name shows `"Name is required."` inline.
2. Empty email shows `"Email is required."` inline.
3. Invalid email format shows `"Please enter a valid email address."` inline.
4. Password < 8 chars shows `"Password must be at least 8 characters."` inline.
5. Valid submission → account created → redirect to `/tasks`.
6. Duplicate email → `"An account with this email already exists."` form-level error.
7. "Sign in →" link navigates to `/sign-in`.

---

### Page 4 — Tasks `/tasks`

**File:** `app/(protected)/tasks/page.tsx`
**Auth:** Required — middleware redirects to `/sign-in` if unauthenticated
**Purpose:** The main application page — view, create, update, delete, and toggle tasks.

#### Layout

```
+-----------------------------------------------------------+
|  Evolution of Todo          [user@email.com]  [Sign Out]  |
+-----------------------------------------------------------+
|                                                           |
|  My Tasks                              [+ Add Task]       |
|                                                           |
|  +-------------------------------------------------------+|
|  |  [ ]  Buy groceries          Milk and eggs        [✎][×]||
|  |  [x]  Submit report                               [✎][×]||
|  |  [ ]  Prepare demo slides    Hackathon II pres... [✎][×]||
|  +-------------------------------------------------------+|
|                                                           |
|  3 task(s)                                                |
|                                                           |
+-----------------------------------------------------------+
```

#### Sections

##### Header

| Element | Behaviour |
|---------|-----------|
| App name "Evolution of Todo" | Static text |
| User email | Displayed from session |
| "Sign Out" button | Calls Better Auth `signOut()` → redirect to `/sign-in` |

##### Task List

| Element | Behaviour |
|---------|-----------|
| Checkbox `[ ]` / `[x]` | Clicking calls `PATCH /api/tasks/{id}/toggle`; optimistic UI update |
| Title text | Displayed as-is |
| Description text (truncated at 40 chars + `...`) | Displayed below or beside title |
| Edit button `✎` | Opens the inline edit form for that task row |
| Delete button `×` | Shows a confirmation dialog before calling `DELETE /api/tasks/{id}` |
| Task count | `"<n> task(s)"` — updates after any mutation |
| Empty state | `"No tasks yet. Add your first task."` when list is empty |

##### Add Task Button

Clicking "Add Task" opens a modal or inline form (implementation choice —
spec requires the form to have title + description fields and a submit button).

#### Add Task Form

```
+----------------------------------+
|  Add Task                   [×]  |
|                                  |
|  Title *                         |
|  [____________________________]  |
|                                  |
|  Description                     |
|  [____________________________]  |
|                                  |
|  [Cancel]          [Add Task]    |
+----------------------------------+
```

| Field | Validation |
|-------|------------|
| Title | Required; 1–200 chars |
| Description | Optional; 0–500 chars |

**Acceptance Criteria:**

1. Submitting a valid form calls `POST /api/tasks` and adds the task to the list without a full page reload.
2. Empty title shows `"Title is required."` inline.
3. Title > 200 chars shows `"Title must be 200 characters or fewer."` inline.
4. Description > 500 chars shows `"Description must be 500 characters or fewer."` inline.
5. Successful add clears the form and closes the modal/inline form.
6. Cancel closes the form without changes.

#### Edit Task Form

The edit form pre-fills with the task's current title and description.

```
+----------------------------------+
|  Edit Task                  [×]  |
|                                  |
|  Title *                         |
|  [Prepare demo slides_________]  |
|                                  |
|  Description                     |
|  [Hackathon II presentation___]  |
|                                  |
|  [Cancel]          [Save]        |
+----------------------------------+
```

**Acceptance Criteria:**

1. Form pre-fills with current values on open.
2. Submitting calls `PUT /api/tasks/{id}` with only changed fields (or `null` for unchanged).
3. Successful save updates the task in the list without a full page reload.
4. Validation mirrors the Add Task form.
5. Cancel closes the form; task list is unchanged.

#### Delete Confirmation

When "×" is clicked, a confirmation dialog appears:

```
+----------------------------------+
|  Delete Task                     |
|                                  |
|  Delete "Prepare demo slides"?   |
|  This cannot be undone.          |
|                                  |
|  [Cancel]          [Delete]      |
+----------------------------------+
```

**Acceptance Criteria:**

1. "Cancel" closes the dialog; task is not deleted.
2. "Delete" calls `DELETE /api/tasks/{id}` and removes the task from the list.
3. The task title is shown in the dialog.

#### Toggle Behaviour

**Acceptance Criteria:**

1. Clicking the checkbox calls `PATCH /api/tasks/{id}/toggle`.
2. The UI updates optimistically (checkbox changes immediately) before the
   server response confirms.
3. If the server returns an error, the checkbox is reverted.

---

## Component Hierarchy

```
app/(protected)/tasks/page.tsx        # Server component — session check + initial data fetch
└── TasksView                         # Client component — all interactivity
    ├── Header
    │   └── SignOutButton
    ├── AddTaskButton → AddTaskForm
    ├── TaskList
    │   └── TaskItem (×n)
    │       ├── TaskCheckbox
    │       ├── TaskEditButton → EditTaskForm
    │       └── TaskDeleteButton → DeleteConfirmDialog
    └── TaskCount
```

---

## API Client (`frontend/lib/api.ts`)

All fetch calls attach the Better Auth session token as `Authorization: Bearer`.
The token is retrieved via `auth.api.getSession()` server-side or
`useSession()` client-side.

| Function | Calls | Returns |
|----------|-------|---------|
| `getTasks(token)` | `GET /api/tasks` | `Task[]` |
| `createTask(token, data)` | `POST /api/tasks` | `Task` |
| `updateTask(token, id, data)` | `PUT /api/tasks/{id}` | `Task` |
| `deleteTask(token, id)` | `DELETE /api/tasks/{id}` | `void` |
| `toggleTask(token, id)` | `PATCH /api/tasks/{id}/toggle` | `Task` |

---

## TypeScript Types

### `Task`

```typescript
interface Task {
  id: number;
  title: string;
  description: string;
  completed: boolean;
  created_at: string;   // ISO 8601 UTC
  updated_at: string;   // ISO 8601 UTC
}
```

### `CreateTaskInput`

```typescript
interface CreateTaskInput {
  title: string;        // required, 1–200 chars
  description?: string; // optional, 0–500 chars
}
```

### `UpdateTaskInput`

```typescript
interface UpdateTaskInput {
  title?: string | null;        // null = keep existing
  description?: string | null;  // null = keep existing
}
```

---

## Error Handling

| Error Condition | UI Behaviour |
|----------------|--------------|
| API returns `400` | Show the `detail` message inline near the relevant field |
| API returns `401` | Redirect to `/sign-in` (session expired) |
| API returns `404` | Show `"Task not found."` toast; refresh task list |
| API returns `500` | Show `"Something went wrong. Please try again."` toast |
| Network error | Show `"Could not connect to the server."` toast |

---

## Loading States

| Action | Loading Indicator |
|--------|------------------|
| Initial page load | Skeleton rows in the task list |
| Add/edit task submit | Spinner on submit button; button disabled |
| Delete confirmation | Spinner on Delete button; button disabled |
| Toggle checkbox | Checkbox disabled until response returns |
| Sign in / sign up | Spinner on submit button; button disabled |

---

## Success Criteria (UI)

| ID | Criterion |
|----|-----------|
| **SC-UI-001** | A new user can sign up and immediately see the empty tasks page. |
| **SC-UI-002** | An existing user can sign in and see their task list. |
| **SC-UI-003** | All 5 task operations are reachable without navigating away from `/tasks`. |
| **SC-UI-004** | The task list updates after every mutation without a full page reload. |
| **SC-UI-005** | Signing out clears the session and redirects to `/sign-in`. |
| **SC-UI-006** | Form validation errors are shown inline before the API is called. |
| **SC-UI-007** | Delete always shows a confirmation dialog before removing the task. |
| **SC-UI-008** | The UI is usable on a 1280×800 desktop viewport. |

---

## Out of Scope (Phase II UI)

- Mobile-responsive / adaptive layout (deferred to Phase III+)
- Dark mode
- Drag-and-drop task reordering
- Task filtering or search input
- Keyboard shortcuts
- Pagination or infinite scroll
- Toast notification library (use `alert()` or a simple inline message)
- Animation / transitions beyond browser defaults

---

## References

| Document | Path |
|----------|------|
| Phase II overview | `specs/overview.md` |
| Auth spec | `specs/features/authentication.md` |
| REST endpoints | `specs/api/rest-endpoints.md` |
| Database schema | `specs/database/schema.md` |
| Global constitution | `.specify/memory/constitution.md` |
