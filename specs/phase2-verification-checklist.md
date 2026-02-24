# Phase II Verification Checklist

**Version:** 1.0.0
**Date:** 2026-02-24
**Phase:** II
**Refs:** `specs/overview.md` · `specs/api/rest-endpoints.md` · `specs/features/authentication.md` · `specs/ui/pages.md` · `specs/database/schema.md`

---

## How to Use This Checklist

- Work through sections in order — prerequisites must pass before API tests, API tests before UI tests.
- Each item has an **expected result** and a **spec reference**.
- Mark `[x]` when the step passes, `[!]` if it fails (note the actual result).
- Stop at the first `[!]` in each section and resolve before continuing.

---

## 0. Prerequisites

### 0.1 Environment files present

- [ ] `backend/.env` exists and contains all four keys:
  - `DATABASE_URL` — SQLite (`sqlite:///./dev.db`) for dev, Neon URL for prod
  - `BETTER_AUTH_SECRET` — non-empty string
  - `AUTH_DISABLED=false`
  - `ALLOWED_ORIGINS=http://localhost:3000`
- [ ] `frontend/.env.local` exists and contains all three keys:
  - `BETTER_AUTH_SECRET` — **identical value** to `backend/.env`
  - `NEXT_PUBLIC_API_URL=http://localhost:8000`
  - `NEXT_PUBLIC_APP_URL=http://localhost:3000`
- [ ] Shared secret matches: `grep BETTER_AUTH_SECRET backend/.env` and `grep BETTER_AUTH_SECRET frontend/.env.local` print the same value.

### 0.2 Services start cleanly

```bash
# Terminal A — backend
cd backend
uv run uvicorn src.app:app --reload --port 8000
# Expected: "Application startup complete." — no import errors

# Terminal B — frontend
cd frontend
npm run dev
# Expected: "✓ Ready on http://localhost:3000" — no compile errors
```

- [ ] Backend starts without errors
- [ ] Frontend starts without errors
- [ ] `http://localhost:8000/docs` loads Swagger UI
- [ ] `http://localhost:3000` redirects to `/sign-in`

### 0.3 Automated test suite passes

```bash
cd backend
uv run pytest -q
# Expected: 144 passed
```

- [ ] All 144 backend tests pass

---

## 1. Backend API Tests

All steps use `curl`. Replace `$TOKEN` with a valid JWT (see §1.0).

### 1.0 Generate a test JWT

```bash
cd backend
uv run python - <<'EOF'
import jwt, datetime, os
from dotenv import load_dotenv
load_dotenv()
secret = os.environ["BETTER_AUTH_SECRET"]
token = jwt.encode(
    {
        "sub": "test-user-manual-001",
        "email": "manual@example.com",
        "name": "Manual Tester",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
    },
    secret,
    algorithm="HS256",
)
print(token)
EOF
```

Copy the printed token and export it:

```bash
export TOKEN="<paste token here>"
```

- [ ] Token prints without error (confirms PyJWT + shared secret work)

### 1.1 Health check

```bash
curl -s http://localhost:8000/health
```

Expected: `{"status":"ok"}` · HTTP 200

- [ ] **SC-P2-001** — Health endpoint responds `200`

### 1.2 Auth guard — no token

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/tasks
```

Expected: `401`

```bash
curl -s http://localhost:8000/api/tasks
```

Expected: `{"detail":"Not authenticated."}`

- [ ] `FR-AUTH-007` — Missing token returns 401 "Not authenticated."

### 1.3 Auth guard — invalid token

```bash
curl -s -H "Authorization: Bearer not-a-jwt" http://localhost:8000/api/tasks
```

Expected: `{"detail":"Invalid token."}` · HTTP 401

- [ ] `FR-AUTH-007` — Bad token returns 401 "Invalid token."

### 1.4 Auth guard — expired token

```bash
cd backend
uv run python - <<'EOF'
import jwt, datetime, os
from dotenv import load_dotenv
load_dotenv()
secret = os.environ["BETTER_AUTH_SECRET"]
token = jwt.encode(
    {"sub": "u1", "exp": datetime.datetime.utcnow() - datetime.timedelta(seconds=1)},
    secret, algorithm="HS256",
)
print(token)
EOF
# Use the printed token:
curl -s -H "Authorization: Bearer <expired-token>" http://localhost:8000/api/tasks
```

Expected: `{"detail":"Token expired."}` · HTTP 401

- [ ] `FR-AUTH-007` — Expired token returns 401 "Token expired."

### 1.5 GET /api/tasks — empty list

```bash
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/tasks
```

Expected: `[]` · HTTP 200

- [ ] Returns empty array for a fresh user, not 404
- [ ] `user_id` field is absent from the response

### 1.6 POST /api/tasks — create task

```bash
curl -s -X POST http://localhost:8000/api/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Buy groceries","description":"Milk and eggs"}'
```

Expected: HTTP 201, response contains:
```json
{
  "id": 1,
  "title": "Buy groceries",
  "description": "Milk and eggs",
  "completed": false,
  "created_at": "<ISO-8601>",
  "updated_at": "<ISO-8601>"
}
```

- [ ] Status is `201`, not `200`
- [ ] `completed` is `false`
- [ ] `id` is a positive integer
- [ ] `user_id` is absent from the response
- [ ] `created_at` and `updated_at` are present

```bash
# Save the task ID:
export TASK_ID=$(curl -s -X POST http://localhost:8000/api/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test task","description":"Desc"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "Task ID: $TASK_ID"
```

### 1.7 POST /api/tasks — validation errors

```bash
# Empty title
curl -s -X POST http://localhost:8000/api/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":""}'
```
Expected: `{"detail":"Title cannot be empty."}` · HTTP 400

```bash
# Whitespace-only title
curl -s -X POST http://localhost:8000/api/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"   "}'
```
Expected: `{"detail":"Title cannot be empty."}` · HTTP 400

```bash
# Title too long (201 chars)
curl -s -X POST http://localhost:8000/api/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"$(python3 -c "print('x'*201)")\"}"
```
Expected: `{"detail":"Title must be 200 characters or fewer."}` · HTTP 400

```bash
# Description too long (501 chars)
curl -s -X POST http://localhost:8000/api/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"ok\",\"description\":\"$(python3 -c "print('x'*501)")\"}"
```
Expected: `{"detail":"Description must be 500 characters or fewer."}` · HTTP 400

- [ ] Empty title → 400 "Title cannot be empty."
- [ ] Whitespace title → 400 "Title cannot be empty."
- [ ] Title > 200 chars → 400 "Title must be 200 characters or fewer."
- [ ] Description > 500 chars → 400 "Description must be 500 characters or fewer."

### 1.8 GET /api/tasks/{id}

```bash
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/tasks/$TASK_ID
```
Expected: HTTP 200, task object with matching `id`

```bash
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/tasks/99999
```
Expected: `404`

- [ ] Existing task returns 200
- [ ] Non-existent ID returns 404 with `"Task #99999 not found."`

### 1.9 PUT /api/tasks/{id} — update

```bash
# Update title only (description null = keep existing)
curl -s -X PUT http://localhost:8000/api/tasks/$TASK_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Updated title","description":null}'
```
Expected: HTTP 200, `"title":"Updated title"`, description unchanged

```bash
# Null both = no changes
curl -s -X PUT http://localhost:8000/api/tasks/$TASK_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```
Expected: HTTP 200, task unchanged

- [ ] `null` title keeps existing value
- [ ] `null` description keeps existing value
- [ ] Empty string `""` title returns 400 "Title cannot be empty."
- [ ] `updated_at` changes after a successful update

### 1.10 PATCH /api/tasks/{id}/toggle

```bash
# Toggle to complete
curl -s -X PATCH \
  -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/tasks/$TASK_ID/toggle
```
Expected: `"completed": true`

```bash
# Toggle back to pending
curl -s -X PATCH \
  -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/tasks/$TASK_ID/toggle
```
Expected: `"completed": false`

- [ ] First toggle: `completed` flips to `true`
- [ ] Second toggle: `completed` flips back to `false`
- [ ] `updated_at` changes after each toggle

### 1.11 DELETE /api/tasks/{id}

```bash
curl -s -X DELETE \
  -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/tasks/$TASK_ID
```
Expected: `{"detail":"Task #<id> deleted."}` · HTTP 200

```bash
# Second delete — task gone
curl -s -o /dev/null -w "%{http_code}" -X DELETE \
  -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/tasks/$TASK_ID
```
Expected: `404`

- [ ] First delete returns 200 with confirmation message
- [ ] Second delete returns 404 (ID never reused)
- [ ] Deleted task no longer in `GET /api/tasks`

### 1.12 User isolation

```bash
# Token for a second user
export TOKEN2=$(cd backend && uv run python - <<'EOF'
import jwt, datetime, os
from dotenv import load_dotenv
load_dotenv()
secret = os.environ["BETTER_AUTH_SECRET"]
print(jwt.encode(
    {"sub": "test-user-manual-002", "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)},
    secret, algorithm="HS256",
))
EOF
)

# Create a task as user 1
export ID1=$(curl -s -X POST http://localhost:8000/api/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"User1 private"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# Attempt to read user 1's task as user 2
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $TOKEN2" \
  http://localhost:8000/api/tasks/$ID1
```
Expected: `404` (not `403` — no information leakage)

```bash
# User 2's task list must not contain user 1's task
curl -s -H "Authorization: Bearer $TOKEN2" http://localhost:8000/api/tasks
```
Expected: `[]` (empty — user 2 has no tasks)

- [ ] `SC-P2-002` — User 2 cannot read User 1's task (404)
- [ ] User 2's task list is isolated

---

## 2. JWT Auth Verification

These checks confirm the token contract between frontend and backend.

### 2.1 Token payload structure

Decode a token issued by the frontend (sign in via UI, then inspect the `auth_token` cookie in DevTools → Application → Cookies).

```bash
# Decode without verifying (inspect only)
node -e "
const t = '<paste-auth_token-cookie-value>';
const [,payload] = t.split('.');
console.log(JSON.parse(Buffer.from(payload, 'base64url').toString()));
"
```

Expected payload shape:
```json
{
  "sub": "<user-uuid>",
  "email": "user@example.com",
  "name": "User Name",
  "iat": <unix-timestamp>,
  "exp": <unix-timestamp-7-days-from-iat>
}
```

- [ ] `sub` claim is present and non-empty (this becomes `user_id` in the backend)
- [ ] `exp` is approximately `iat + 604800` (7 days in seconds)
- [ ] Algorithm header is `{"alg":"HS256","typ":"JWT"}`

### 2.2 Token accepted by backend

```bash
# Extract auth_token from browser (copy from DevTools)
export BROWSER_TOKEN="<auth_token cookie value>"
curl -s -H "Authorization: Bearer $BROWSER_TOKEN" http://localhost:8000/api/tasks
```

Expected: HTTP 200, JSON array (not 401)

- [ ] `FR-AUTH-011` — Token issued by Next.js frontend is accepted by FastAPI backend (shared secret works)

### 2.3 Wrong-secret token rejected

```bash
uv run python - <<'EOF'
import jwt, datetime
token = jwt.encode(
    {"sub": "u1", "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)},
    "wrong-secret",
    algorithm="HS256",
)
print(token)
EOF
curl -s -H "Authorization: Bearer <wrong-secret-token>" http://localhost:8000/api/tasks
```

Expected: `{"detail":"Invalid token."}` · HTTP 401

- [ ] `FR-AUTH-007` — Token signed with a different secret is rejected

### 2.4 Cookie is httpOnly

Open DevTools → Console in the browser, run:

```javascript
document.cookie
```

Expected: `auth_token` does **not** appear in `document.cookie`

- [ ] Cookie is httpOnly (not accessible to JavaScript)

### 2.5 AUTH_DISABLED bypass (dev only)

```bash
# In backend/.env, temporarily set AUTH_DISABLED=true, then restart uvicorn
curl -s http://localhost:8000/api/tasks
# Expected: 200 [] (no Authorization header needed)
# Revert AUTH_DISABLED=false before continuing
```

- [ ] `AUTH_DISABLED=true` bypasses validation (useful for API exploration)
- [ ] `AUTH_DISABLED=false` (default) — all protected routes require a valid JWT

---

## 3. Neon Database Connection Test

Run these steps when switching from SQLite to Neon PostgreSQL.

### 3.1 Obtain Neon connection string

- [ ] Log in to console.neon.tech
- [ ] Create or select a project
- [ ] Copy the connection string (Settings → Connection Details):
  ```
  postgresql+psycopg2://user:password@<host>.neon.tech/<db>?sslmode=require
  ```

### 3.2 Update environment files

```bash
# backend/.env
DATABASE_URL=postgresql+psycopg2://user:password@<host>.neon.tech/neondb?sslmode=require
BETTER_AUTH_SECRET=<generate: python -c "import secrets; print(secrets.token_hex(32))">

# frontend/.env.local
BETTER_AUTH_SECRET=<same value as above>
```

- [ ] Both files updated with the same `BETTER_AUTH_SECRET`
- [ ] `DATABASE_URL` points to Neon (not SQLite)

### 3.3 Test PostgreSQL connection

```bash
cd backend
uv run python - <<'EOF'
from dotenv import load_dotenv
load_dotenv()
from src.database import engine, create_db_and_tables
create_db_and_tables()
print("Tables created successfully")
from sqlmodel import Session, text
with Session(engine) as s:
    result = s.exec(text("SELECT tablename FROM pg_tables WHERE schemaname='public'")).all()
    print("Tables:", [r[0] for r in result])
EOF
```

Expected output:
```
Tables created successfully
Tables: ['task']
```

- [ ] `create_db_and_tables()` runs without error
- [ ] `task` table is present in Neon (verify in Neon console → Tables)
- [ ] No SSL errors

### 3.4 Neon table schema

In the Neon console (Tables → `task`), verify all columns exist:

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| `id` | integer | NO | nextval |
| `title` | varchar(200) | NO | — |
| `description` | varchar(500) | NO | `''` |
| `completed` | boolean | NO | `false` |
| `user_id` | varchar | NO | — |
| `created_at` | timestamp | NO | — |
| `updated_at` | timestamp | NO | — |

- [ ] All 7 columns present with correct types and constraints
- [ ] Index `ix_task_user_id` exists on `user_id`

### 3.5 Data written to Neon

```bash
# Re-run backend with Neon DATABASE_URL, then:
export TOKEN=$(cd backend && uv run python - <<'EOF'
import jwt, datetime, os
from dotenv import load_dotenv; load_dotenv()
print(jwt.encode({"sub":"neon-test-001","exp":datetime.datetime.utcnow()+datetime.timedelta(hours=1)},os.environ["BETTER_AUTH_SECRET"],algorithm="HS256"))
EOF
)
curl -s -X POST http://localhost:8000/api/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Neon persistence test"}'
```

Then check Neon console → Tables → `task` — the row must appear.

- [ ] Row is visible in the Neon console after the POST request
- [ ] Restarting the backend server and calling `GET /api/tasks` still returns the row (persistent)

---

## 4. Frontend UI Test Steps

Run with backend at `http://localhost:8000` and frontend at `http://localhost:3000`.

### 4.1 Root redirect

- [ ] `http://localhost:3000/` redirects to `/sign-in` (not authenticated)
- [ ] No content flash before redirect

### 4.2 Sign-up page (`/sign-up`)

**Inline validation (client-side, before submit):**

- [ ] Submit with all fields empty → `"Name is required."` appears inline
- [ ] Fill name, submit with empty email → `"Email is required."` appears inline
- [ ] Enter invalid email format (e.g. `notanemail`) → `"Please enter a valid email address."` inline
- [ ] Enter valid email, submit with empty password → `"Password is required."` inline
- [ ] Enter password of 7 chars → `"Password must be at least 8 characters."` inline
- [ ] Submit button shows spinner and is disabled during the request

**Server-side validation:**

- [ ] Valid name + email + password (≥ 8 chars) → account created → redirect to `/tasks`
- [ ] Same email a second time → `"An account with this email already exists."` form-level error
- [ ] `"Already have an account? Sign in →"` link navigates to `/sign-in`

**Acceptance criteria refs:** `specs/features/authentication.md §US-AUTH-01`

### 4.3 Sign-in page (`/sign-in`)

**Inline validation:**

- [ ] Submit empty form → `"Email is required."` inline
- [ ] Invalid email format → `"Please enter a valid email address."` inline
- [ ] Empty password → `"Password is required."` inline
- [ ] Submit button disabled and shows spinner during request

**Server-side:**

- [ ] Correct credentials → redirect to `/tasks`
- [ ] Wrong password → `"Invalid email or password."` form-level (no redirect)
- [ ] Unregistered email → `"Invalid email or password."` (same message — no account enumeration)
- [ ] `"Don't have an account? Sign up →"` link navigates to `/sign-up`
- [ ] Visiting `/sign-in` while already authenticated → redirected to `/tasks`

**Acceptance criteria refs:** `specs/features/authentication.md §US-AUTH-02`

### 4.4 Tasks page (`/tasks`) — initial state

- [ ] Header shows app name `"Evolution of Todo"`
- [ ] Header shows signed-in user's email
- [ ] `"+ Add Task"` button is visible
- [ ] Empty state message: `"No tasks yet. Add your first task."`
- [ ] Task count reads `"0 task(s)"`

### 4.5 Add task form

- [ ] Clicking `"+ Add Task"` opens the modal
- [ ] Empty title → `"Title is required."` inline
- [ ] Title > 200 chars → `"Title must be 200 characters or fewer."` inline
- [ ] Description > 500 chars → `"Description must be 500 characters or fewer."` inline
- [ ] Submit button shows spinner and is disabled during the request
- [ ] Valid title + description → task appears in list without page reload
- [ ] `"Cancel"` closes modal without changes
- [ ] Task count increments after add

**Acceptance criteria refs:** `specs/ui/pages.md §Add Task Form`

### 4.6 Task list

- [ ] Each task row shows: checkbox `[ ]`, title, truncated description (≤ 40 chars + `…`), edit `✎`, delete `×`
- [ ] Completed tasks show strikethrough title

### 4.7 Toggle checkbox

- [ ] Clicking checkbox immediately changes its visual state (optimistic update)
- [ ] Backend confirms — checkbox stays in new state
- [ ] If backend returns an error, checkbox reverts to original state
- [ ] Checkbox is disabled while the request is in flight (no double-click)

**Acceptance criteria refs:** `specs/ui/pages.md §Toggle Behaviour`

### 4.8 Edit task

- [ ] Clicking `✎` opens the Edit modal pre-filled with current title and description
- [ ] Changing only the title and saving → title updates, description unchanged
- [ ] `"Cancel"` closes modal, task list unchanged
- [ ] Save button shows spinner during request
- [ ] Updated task reflects in list without page reload

**Acceptance criteria refs:** `specs/ui/pages.md §Edit Task Form`

### 4.9 Delete task

- [ ] Clicking `×` opens confirmation dialog showing task title
- [ ] Dialog shows `"Delete "<title>"?"` and `"This cannot be undone."`
- [ ] `"Cancel"` closes dialog, task still in list
- [ ] `"Delete"` removes task from list without page reload
- [ ] Delete button shows spinner and is disabled during request

**Acceptance criteria refs:** `specs/ui/pages.md §Delete Confirmation`

### 4.10 Sign out

- [ ] Clicking `"Sign Out"` clears the session cookie
- [ ] Redirected to `/sign-in`
- [ ] Navigating to `/tasks` after sign-out redirects to `/sign-in`

**Acceptance criteria refs:** `specs/features/authentication.md §US-AUTH-03`

### 4.11 Protected route enforcement

- [ ] Navigating to `http://localhost:3000/tasks` without a session → redirected to `/sign-in`
- [ ] After session expires (test by manually deleting `auth_token` cookie) → next page load redirects to `/sign-in`

**Acceptance criteria refs:** `specs/features/authentication.md §US-AUTH-04`

### 4.12 Error handling

- [ ] Stop the backend server, then try to add a task → toast `"Could not connect to the server."`
- [ ] Restart backend, then observe that tasks reload on next interaction

---

## 5. End-to-End Persistence Flow

**Scenario:** Sign up → Create tasks → Sign out → Sign in → Verify tasks persisted

### Step 1 — Sign up as a new user

1. Navigate to `http://localhost:3000/sign-up`
2. Enter name `"Alice Test"`, email `"alice@example.com"`, password `"password123"`
3. Click `"Create Account"`

- [ ] Redirected to `/tasks`
- [ ] Header shows `alice@example.com`
- [ ] Empty task list (0 task(s))

### Step 2 — Create three tasks

4. Click `"+ Add Task"`, enter:
   - Title: `"Buy groceries"`, Description: `"Milk and eggs"` → Add
5. Click `"+ Add Task"`, enter:
   - Title: `"Submit report"`, Description: `""` → Add
6. Click `"+ Add Task"`, enter:
   - Title: `"Prepare demo slides"`, Description: `"Hackathon II presentation"` → Add

- [ ] All three tasks appear in the list in creation order
- [ ] Task count reads `"3 task(s)"`

### Step 3 — Mutate state

7. Toggle `"Submit report"` → mark as complete
8. Edit `"Buy groceries"` → change description to `"Milk, eggs, and bread"` → Save

- [ ] `"Submit report"` shows strikethrough and `[x]`
- [ ] `"Buy groceries"` description updates to `"Milk, eggs, and bread…"` (truncated)

### Step 4 — Sign out

9. Click `"Sign Out"` in the header

- [ ] Redirected to `/sign-in`

### Step 5 — Sign back in

10. Enter `alice@example.com` / `password123`
11. Click `"Sign In"`

- [ ] Redirected to `/tasks`

### Step 6 — Verify persistence

- [ ] **SC-P2-003** — All 3 tasks are present (data survived a sign-out/sign-in cycle)
- [ ] `"Submit report"` is still marked complete `[x]`
- [ ] `"Buy groceries"` description still shows the updated value
- [ ] Task count is `"3 task(s)"`
- [ ] Task IDs match the original creation order (ascending)

### Step 7 — User isolation check

12. Sign out
13. Navigate to `/sign-up`, register as `"bob@example.com"` / `"password123"`

- [ ] Bob's task list is empty (`"0 task(s)"`)
- [ ] Alice's tasks are not visible to Bob (**SC-P2-004** + user isolation)

---

## 6. Success Criteria Summary

All of the following must be `[x]` before Phase II is considered complete.

| ID | Criterion | Section |
|----|-----------|---------|
| **SC-P2-001** | Sign up, sign in, and sign out work via the web UI | §4.2, §4.3, §4.10 |
| **SC-P2-002** | All 5 task operations work via REST API with a valid token | §1.6–§1.11 |
| **SC-P2-003** | Tasks survive a server restart (persistent storage) | §5 Step 6 |
| **SC-P2-004** | Unauthenticated requests to `/api/tasks` return HTTP 401 | §1.2 |
| **SC-P2-005** | Task list UI reflects all mutations without full page reload | §4.5–§4.9 |
| **SC-P2-006** | All 144 Phase I + Phase II tests pass | §0.3 |
| **SC-P2-007** | `uv run todo` (Phase I console app) still boots | run from repo root |
| **SC-P2-008** | No secrets in source code or committed to git | `git grep SECRET` returns nothing |

### SC-P2-007 — Phase I console still works

```bash
cd /path/to/Hackathon2-todo   # repo root
uv run todo
```

- [ ] Main menu appears and all 5 options respond correctly

### SC-P2-008 — No secrets in source

```bash
git grep -r "BETTER_AUTH_SECRET\s*=" -- '*.py' '*.ts' '*.tsx' '*.js'
```

Expected: no matches (secrets must only appear in `.env` / `.env.local`, which are in `.gitignore`)

- [ ] No secrets committed to the repository

---

## 7. Known Limitations (Out of Scope for Phase II)

The following are intentional non-goals and should **not** be treated as failures:

- Mobile/responsive layout (deferred to Phase III)
- Password reset / forgot password flow
- OAuth / social sign-in
- Email verification
- Task filtering, sorting, or search
- Pagination or infinite scroll
- Alembic migrations (using `create_all` for Phase II)
- Real-time updates (WebSockets / SSE)
- Toast notification library (simple inline messages only)
- Dark mode

---

## References

| Document | Path |
|----------|------|
| Phase II overview | `specs/overview.md` |
| REST endpoints | `specs/api/rest-endpoints.md` |
| Auth spec | `specs/features/authentication.md` |
| UI pages | `specs/ui/pages.md` |
| Database schema | `specs/database/schema.md` |
