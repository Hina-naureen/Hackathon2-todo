---
id: "027"
title: "Phase III Chat API Spec and Stub"
stage: general
date: "2026-02-25"
surface: agent
model: claude-sonnet-4-6
feature: "none"
branch: master
user: Hina-naureen
command: "Create Phase III backend chat API spec + minimal implementation"
labels: ["phase-iii", "chat-api", "fastapi", "spec", "tests", "backend"]
links:
  spec: "specs/api/chat-endpoint.md"
  ticket: "null"
  adr: "null"
  pr: "null"
files:
  - "specs/api/chat-endpoint.md"
  - "backend/src/routes/chat.py"
  - "backend/src/app.py"
  - "backend/tests/test_chat.py"
tests:
  - "tests/test_chat.py::TestChat::test_valid_message_returns_200"
  - "tests/test_chat.py::TestChat::test_reply_echoes_message"
  - "tests/test_chat.py::TestChat::test_reply_strips_whitespace_from_message"
  - "tests/test_chat.py::TestChat::test_trace_id_is_present"
  - "tests/test_chat.py::TestChat::test_trace_id_is_unique_per_request"
  - "tests/test_chat.py::TestChat::test_response_has_reply_and_trace_id_fields"
  - "tests/test_chat.py::TestChat::test_empty_message_returns_400"
  - "tests/test_chat.py::TestChat::test_whitespace_only_message_returns_400"
  - "tests/test_chat.py::TestChatAuth::test_missing_token_returns_401"
  - "tests/test_chat.py::TestChatAuth::test_invalid_token_returns_401"
---

## Prompt

Create Phase III backend chat API spec + minimal implementation.

Create spec:
@specs/api/chat-endpoint.md

Spec requirements:
- POST /api/chat
- Auth required (JWT)
- Request body: { "message": string }
- Response: { "reply": string, "trace_id": string }

Implementation requirements (backend only):
- Create route in FastAPI under /api/chat
- Verify JWT (same auth approach as tasks)
- For now reply should be deterministic echo:
  reply = "You said: <message>"
- Add tests for /api/chat (401 without token, 200 with token)
- Do not add OpenAI yet

After spec, implement it in backend.
Do not change frontend yet.

## Response

Created spec, route, registered it in app, and added 10 tests. All 10 new tests
pass; all 37 pre-existing tests continue to pass (zero regressions).

### specs/api/chat-endpoint.md (new)
Full spec following the format of `specs/api/rest-endpoints.md`. Covers:
- Endpoint contract (request/response schemas, error table)
- Acceptance criteria (AC-1 through AC-7)
- Phase III stub vs production comparison table
- Implementation notes pointing to route and test files

### backend/src/routes/chat.py (new)
- `ChatRequest(BaseModel)`: `message: str`
- `ChatResponse(BaseModel)`: `reply: str`, `trace_id: str`
- `POST /` handler: strips message, raises `400` if empty, returns echo reply + `uuid.uuid4()` trace_id
- Auth via `Depends(get_current_user)` — identical dependency to tasks routes
- No database interaction; no OpenAI call

### backend/src/app.py (modified)
- Added `from src.routes.chat import router as chat_router`
- Added `app.include_router(chat_router, prefix="/api/chat", tags=["chat"])`
- No other changes

### backend/tests/test_chat.py (new)
Two test classes:
- `TestChat` (8 tests): 200 happy path, echo correctness, whitespace strip, trace_id present, trace_id unique per request, response field set, 400 empty message, 400 whitespace-only message
- `TestChatAuth` (2 tests): 401 missing token, 401 invalid token

Auth override pattern mirrors `test_api.py::TestAuth` — clears `dependency_overrides` and uses a bare `TestClient` with no session override (chat route has no DB dependency).

## Outcome

- [x] `specs/api/chat-endpoint.md` created with full contract
- [x] `POST /api/chat` route live and verified
- [x] JWT auth enforced — same dependency as tasks
- [x] Echo stub: `reply = "You said: <message>"`
- [x] `trace_id` is UUID v4, unique per request
- [x] 10/10 new tests pass
- [x] 37/37 existing tests unaffected
- [x] Frontend unchanged
- [x] No OpenAI dependency added
