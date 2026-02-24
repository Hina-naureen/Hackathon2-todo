---
id: 015
title: JWT Verification Middleware Skeleton FastAPI
stage: green
date: 2026-02-24
surface: agent
model: claude-sonnet-4-6
feature: backend-auth
branch: master
user: pc
command: Prepare JWT verification middleware skeleton for FastAPI. Do not finalize secrets yet.
labels: ["backend","fastapi","jwt","auth","middleware","skeleton"]
links:
  spec: specs/features/authentication.md
  ticket: null
  adr: null
  pr: null
files:
  - backend/src/auth/dependencies.py (updated — added load_dotenv() for import-order safety)
  - backend/.env (created — SQLite dev config + placeholder BETTER_AUTH_SECRET)
tests:
  - uv run pytest tests/test_api.py::TestAuth — 2 passed
  - uv run pytest — 144 passed, 0 failed
---

## Prompt

Prepare JWT verification middleware skeleton for FastAPI.
Do not finalize secrets yet.

## Response snapshot

The JWT verification skeleton in `src/auth/dependencies.py` was already implemented
and spec-compliant. Audited it and fixed one robustness issue, then created the
missing `backend/.env`.

### What the skeleton does

| Concern | Implementation |
|---------|----------------|
| Token extraction | `HTTPBearer(auto_error=False)` — returns `None` instead of raising on missing header |
| Missing token | Raises `HTTP 401 "Not authenticated."` |
| Expired token | Catches `jwt.ExpiredSignatureError` → `HTTP 401 "Token expired."` |
| Invalid token | Catches `jwt.PyJWTError` → `HTTP 401 "Invalid token."` |
| Missing sub claim | Raises `HTTP 401 "Invalid token."` |
| Algorithm | HS256 (PyJWT) |
| Dev bypass | `AUTH_DISABLED=true` returns `"dev-user"` without validation |

All error messages match `specs/features/authentication.md §Error Catalogue` and
`specs/api/rest-endpoints.md §Error Taxonomy` exactly.

### Fix applied — `load_dotenv()` in `dependencies.py`

`BETTER_AUTH_SECRET` was read at module-import time but `load_dotenv()` was only
called in `database.py`. If `dependencies.py` is imported independently (e.g., in
tests or future tooling), it would fall back to the hardcoded default even if a real
secret was present in `.env`. Added `load_dotenv()` directly to `dependencies.py`
so the secret is always loaded from the right source regardless of import order.

### `backend/.env` — placeholder, not finalized

Secret intentionally left as `dev-secret-change-in-production` (matches the
frontend's `.env.local` default). A real secret must be generated and set in both
files before the full auth flow is tested end-to-end.

```
TODO: python -c "import secrets; print(secrets.token_hex(32))"
      → set in backend/.env  (BETTER_AUTH_SECRET=<value>)
      → set in frontend/.env.local (BETTER_AUTH_SECRET=<same value>)
```

## Outcome

- ✅ Impact: JWT middleware skeleton is spec-compliant and robust against import order. Backend is ready to validate tokens issued by the Next.js frontend once both sides share the same finalized secret.
- 🧪 Tests: 144/144 passed. Auth-specific tests: TestAuth::test_missing_token_returns_401 PASS, TestAuth::test_invalid_token_returns_401 PASS.
- 📁 Files: 1 updated, 1 created.
- 🔁 Next prompts: Generate a real shared secret and set it in both .env files; then run the full sign-up → task CRUD → sign-out integration test.
- 🧠 Reflection: The skeleton was already correct; the only gap was import-order robustness and the missing .env file. Secrets intentionally deferred per user instruction.

## Evaluation notes (flywheel)

- Failure modes observed: none — all tests green
- Graders run and results (PASS/FAIL): uv run pytest PASS (144/144)
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): Set a real BETTER_AUTH_SECRET in both .env files and run end-to-end auth flow test
