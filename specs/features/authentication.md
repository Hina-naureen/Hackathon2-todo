# Feature Specification: Authentication — Phase II

**Version:** 1.0.0
**Date:** 2026-02-24
**Status:** Draft
**Stage:** spec
**Phase:** II
**Stack:** Better Auth (Next.js 16) + FastAPI JWT validation
**Overview:** `specs/overview.md`
**Constitution:** `.specify/memory/constitution.md`

---

## Overview

Phase II introduces user accounts. Every task is owned by a user. Users
authenticate with email and password via **Better Auth** on the Next.js frontend.
The FastAPI backend validates the resulting JWT on every protected request.

No social login, no OAuth, no magic links in Phase II. Email + password only.

---

## User Stories

---

### US-AUTH-01 — Sign Up (Priority: P1)

A new visitor wants to create an account so they can start managing tasks.
They navigate to `/sign-up`, enter their name, email, and password, submit the
form, and are redirected to the task list on success.

**Acceptance Scenarios:**

1. **Given** a visitor on `/sign-up`, **When** they submit a valid name, email,
   and password (≥ 8 characters), **Then** a user account is created, a session
   is established, and they are redirected to `/tasks`.

2. **Given** a visitor on `/sign-up`, **When** they submit an email that already
   exists, **Then** no account is created and the form displays
   `"An account with this email already exists."`.

3. **Given** a visitor on `/sign-up`, **When** they submit an empty email,
   **Then** the form displays `"Email is required."` and does not submit.

4. **Given** a visitor on `/sign-up`, **When** they submit a password shorter
   than 8 characters, **Then** the form displays
   `"Password must be at least 8 characters."` and does not submit.

5. **Given** a visitor on `/sign-up`, **When** they submit an invalid email
   format, **Then** the form displays `"Please enter a valid email address."`
   and does not submit.

6. **Given** a visitor on `/sign-up`, **When** they submit an empty name,
   **Then** the form displays `"Name is required."` and does not submit.

---

### US-AUTH-02 — Sign In (Priority: P1)

A returning user wants to access their tasks. They navigate to `/sign-in`,
enter their email and password, and are redirected to `/tasks` on success.

**Acceptance Scenarios:**

1. **Given** a registered user on `/sign-in`, **When** they submit their correct
   email and password, **Then** a session is established and they are redirected
   to `/tasks`.

2. **Given** a visitor on `/sign-in`, **When** they submit an email that is not
   registered, **Then** no session is created and the form displays
   `"Invalid email or password."`.

3. **Given** a registered user on `/sign-in`, **When** they submit the wrong
   password, **Then** no session is created and the form displays
   `"Invalid email or password."` (same message — no account enumeration).

4. **Given** a visitor on `/sign-in`, **When** they submit empty fields,
   **Then** the form displays field-level required errors and does not submit.

5. **Given** an authenticated user visiting `/sign-in`, **When** the page
   loads, **Then** they are redirected to `/tasks` immediately (no re-login
   needed).

---

### US-AUTH-03 — Sign Out (Priority: P2)

An authenticated user wants to end their session. They click "Sign Out" from
the task page header and are redirected to `/sign-in`.

**Acceptance Scenarios:**

1. **Given** an authenticated user, **When** they click "Sign Out", **Then**
   the session is invalidated, all local session state is cleared, and they are
   redirected to `/sign-in`.

2. **Given** a signed-out user visiting `/tasks`, **When** the page loads,
   **Then** they are redirected to `/sign-in` by the middleware.

3. **Given** a signed-out user who has the `/tasks` URL bookmarked, **When**
   they navigate there, **Then** they are redirected to `/sign-in`.

---

### US-AUTH-04 — Protected Routes (Priority: P1)

All task-related pages and API endpoints must be inaccessible without a valid
session/token. Anonymous access returns a redirect (UI) or HTTP 401 (API).

**Acceptance Scenarios:**

1. **Given** an unauthenticated browser request to `/tasks`, **When** the
   middleware runs, **Then** the request is redirected to `/sign-in`.

2. **Given** an API request to `GET /api/tasks` without an `Authorization`
   header, **When** FastAPI processes the request, **Then** it returns
   `HTTP 401 Unauthorized` with body `{"detail": "Not authenticated."}`.

3. **Given** an API request to any `/api/tasks` endpoint with an expired JWT,
   **When** FastAPI processes the request, **Then** it returns
   `HTTP 401 Unauthorized` with body `{"detail": "Token expired."}`.

4. **Given** an API request with a JWT signed by a different secret,
   **When** FastAPI processes the request, **Then** it returns
   `HTTP 401 Unauthorized` with body `{"detail": "Invalid token."}`.

5. **Given** an authenticated user, **When** they make any task API call with
   a valid token, **Then** only their own tasks are returned or modified —
   never another user's tasks.

---

## Requirements

### Functional Requirements

| ID | Requirement |
|----|-------------|
| **FR-AUTH-001** | The system MUST support user registration with name, email, and password. |
| **FR-AUTH-002** | Passwords MUST be hashed before storage — never stored in plaintext. |
| **FR-AUTH-003** | Password MUST be ≥ 8 characters. No other complexity rules in Phase II. |
| **FR-AUTH-004** | The system MUST issue a JWT session token on successful sign-in or sign-up. |
| **FR-AUTH-005** | The JWT MUST contain the user's `id` in the `sub` claim. |
| **FR-AUTH-006** | The JWT MUST have an expiry (`exp` claim). Default: 7 days. |
| **FR-AUTH-007** | The system MUST validate the JWT on every protected FastAPI endpoint. |
| **FR-AUTH-008** | Sign-out MUST invalidate the current session on the Better Auth server side. |
| **FR-AUTH-009** | The Next.js middleware MUST redirect unauthenticated users from `/tasks` to `/sign-in`. |
| **FR-AUTH-010** | Each user's tasks MUST be isolated — a user can only read/write their own tasks. |
| **FR-AUTH-011** | The `BETTER_AUTH_SECRET` MUST be identical on both Next.js and FastAPI sides. |
| **FR-AUTH-012** | All auth secrets MUST be stored in `.env` / `.env.local` and MUST NOT be committed to git. |

---

## Error Catalogue

| Trigger | Message / Response |
|---------|-------------------|
| Empty email on sign-up/sign-in | `"Email is required."` |
| Invalid email format | `"Please enter a valid email address."` |
| Empty password | `"Password is required."` |
| Password < 8 characters | `"Password must be at least 8 characters."` |
| Empty name on sign-up | `"Name is required."` |
| Duplicate email on sign-up | `"An account with this email already exists."` |
| Wrong email or password on sign-in | `"Invalid email or password."` |
| No Authorization header on API call | `HTTP 401` · `{"detail": "Not authenticated."}` |
| Expired JWT | `HTTP 401` · `{"detail": "Token expired."}` |
| Invalid JWT signature | `HTTP 401` · `{"detail": "Invalid token."}` |

---

## Auth Flow Diagram

```
Sign Up / Sign In
      │
      ▼
┌─────────────────────────────┐
│  Next.js /sign-in page      │
│  Better Auth client SDK     │
│  POST /api/auth/sign-in     │
└──────────────┬──────────────┘
               │ credentials
               ▼
┌─────────────────────────────┐
│  Better Auth server         │
│  /api/auth/[...all]         │
│  Verifies credentials       │
│  Issues JWT (HS256)         │
│  Sets httpOnly cookie /     │
│  returns token              │
└──────────────┬──────────────┘
               │ JWT token
               ▼
┌─────────────────────────────┐
│  Next.js /tasks page        │
│  Attaches Bearer token      │
│  to every fetch to FastAPI  │
└──────────────┬──────────────┘
               │ Authorization: Bearer <jwt>
               ▼
┌─────────────────────────────┐
│  FastAPI                    │
│  HTTPBearer dependency      │
│  Decodes JWT with shared    │
│  BETTER_AUTH_SECRET         │
│  Extracts user_id from sub  │
│  Passes user_id to handler  │
└─────────────────────────────┘
```

---

## Better Auth Configuration

### Next.js side (`frontend/lib/auth.ts`)

| Config Key | Value |
|------------|-------|
| Provider | `emailAndPassword` — enabled |
| Database | Neon DB (same instance as tasks, separate tables) |
| Secret | `BETTER_AUTH_SECRET` (env var, min 32 chars) |
| Base URL | `NEXT_PUBLIC_APP_URL` (e.g. `http://localhost:3000`) |
| JWT algorithm | HS256 |
| Session expiry | 7 days |
| Session strategy | JWT (stateless) |

### FastAPI side (`backend/src/auth/dependencies.py`)

| Config Key | Value |
|------------|-------|
| Library | `PyJWT` |
| Algorithm | HS256 |
| Secret | `BETTER_AUTH_SECRET` (same value via `backend/.env`) |
| Token source | `Authorization: Bearer <token>` header |
| Extracted claim | `sub` → `user_id: str` |

---

## Better Auth Database Tables

Better Auth auto-creates these tables in Neon DB during setup:

| Table | Key Columns |
|-------|-------------|
| `user` | `id` (str), `name`, `email`, `emailVerified`, `createdAt`, `updatedAt` |
| `session` | `id`, `userId`, `token`, `expiresAt`, `ipAddress`, `userAgent` |
| `account` | `id`, `userId`, `accountId`, `providerId`, `password` (hashed) |
| `verification` | `id`, `identifier`, `value`, `expiresAt` |

The `Task.user_id` column references `user.id` (string UUID). No foreign key
constraint in Phase II (YAGNI), but the value is always populated from the
validated JWT `sub` claim.

---

## Route Protection Matrix

| Route | Authentication | Behaviour if Unauthenticated |
|-------|---------------|------------------------------|
| `/` | None required | Redirect to `/sign-in` |
| `/sign-in` | None required | Show form (redirect to `/tasks` if already signed in) |
| `/sign-up` | None required | Show form (redirect to `/tasks` if already signed in) |
| `/tasks` | Required | Redirect to `/sign-in` |
| `GET /api/tasks` | Required (Bearer JWT) | `HTTP 401` |
| `POST /api/tasks` | Required (Bearer JWT) | `HTTP 401` |
| `PUT /api/tasks/{id}` | Required (Bearer JWT) | `HTTP 401` |
| `DELETE /api/tasks/{id}` | Required (Bearer JWT) | `HTTP 401` |
| `PATCH /api/tasks/{id}/toggle` | Required (Bearer JWT) | `HTTP 401` |
| `POST /api/auth/*` | None required | Better Auth handler |

---

## Out of Scope (Phase II Auth)

- OAuth / social providers (Google, GitHub, etc.)
- Magic link / passwordless sign-in
- Email verification flow
- Password reset / forgot password
- Multi-factor authentication (MFA)
- Role-based access control (RBAC)
- Refresh token rotation
- IP-based rate limiting

---

## References

| Document | Path |
|----------|------|
| Phase II overview | `specs/overview.md` |
| REST endpoints | `specs/api/rest-endpoints.md` |
| Database schema | `specs/database/schema.md` |
| UI pages | `specs/ui/pages.md` |
| Global constitution | `.specify/memory/constitution.md` |
