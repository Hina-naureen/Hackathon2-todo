---
id: "030"
title: "Chat Safe Mode Fallback"
stage: general
date: "2026-02-25"
surface: agent
model: claude-sonnet-4-6
feature: "none"
branch: master
user: Hina-naureen
command: "Fix /api/chat endpoint to run in SAFE MODE"
labels: ["phase-iii", "chat-api", "resilience", "error-handling", "backend"]
links:
  spec: "specs/api/chat-endpoint.md"
  ticket: "null"
  adr: "null"
  pr: "null"
files:
  - "backend/src/routes/chat.py"
  - "backend/tests/test_chat.py"
tests:
  - "tests/test_chat.py::TestChatSafeMode::test_agent_exception_returns_200_with_echo"
  - "tests/test_chat.py::TestChatSafeMode::test_missing_api_key_returns_200_with_echo"
  - "tests/test_chat.py::TestChatSafeMode::test_echo_uses_stripped_message"
---

## Prompt

Fix /api/chat endpoint to run in SAFE MODE.

Rules:
- If AI agent fails, fallback to echo reply: reply = "You said: <message>"
- Wrap agent execution in try/except.
- Log error to console but do not crash API.
- Always return 200 response.

Do not remove agent code. Just add graceful fallback.

## Response

### backend/src/routes/chat.py (2 changes)

1. Added `import logging` and `logger = logging.getLogger(__name__)`.

2. Wrapped the agent instantiation and `agent.run()` call in try/except:
   ```python
   actions: list[ActionTrace] = []
   try:
       agent = TaskAgent(session, user_id)
       reply, actions = await agent.run(message)
   except Exception as exc:
       logger.error("Agent failed for user %s — falling back to echo: %s", user_id, exc)
       reply = f"You said: {message}"
   ```
   - `actions` is pre-initialised to `[]` so the response always serialises cleanly.
   - The `except` clause catches everything: `HTTPException` (e.g. 503 from missing key),
     `RuntimeError`, network errors, etc.
   - 400 for empty messages is still raised before the try block — correct.
   - The `return ChatResponse(...)` is outside the try block — always executes.

### backend/tests/test_chat.py (new class TestChatSafeMode, 3 tests)

- `test_agent_exception_returns_200_with_echo`: monkeypatches `_call_llm` to raise
  `RuntimeError`; asserts 200, echo reply, empty actions list.
- `test_missing_api_key_returns_200_with_echo`: monkeypatches `_call_llm` to raise
  `HTTPException(503)`; asserts 200, echo reply.
- `test_echo_uses_stripped_message`: verifies the fallback echo uses the already-stripped
  `message` variable (not the raw `body.message`).

## Outcome

- [x] Agent code untouched (agent.py, tools.py, prompts.py unchanged)
- [x] All agent failures → 200 with echo reply
- [x] Error logged via `logger.error(...)` (stderr in dev, log aggregator in prod)
- [x] Empty message still returns 400 (not caught by safe mode)
- [x] 401 without token still works (FastAPI auth runs before the route body)
- [x] 14/14 chat tests pass
- [x] 194/194 total tests pass (zero regressions)
