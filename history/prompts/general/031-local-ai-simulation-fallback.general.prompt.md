---
id: "031"
title: "Local AI Simulation Fallback"
stage: general
date: "2026-02-25"
surface: agent
model: claude-sonnet-4-6
feature: "none"
branch: master
user: Hina-naureen
command: "Refactor Chat Safe Mode to simulate AI responses without OpenAI API"
labels: ["phase-iii", "agent", "simulation", "fallback", "backend"]
links:
  spec: "specs/agents/agent-behavior.md"
  ticket: "null"
  adr: "null"
  pr: "null"
files:
  - "backend/agents/agent.py"
  - "backend/tests/test_agent.py"
tests:
  - "tests/test_agent.py::TestLocalSimulation::test_add_keyword_returns_task_creation_reply"
  - "tests/test_agent.py::TestLocalSimulation::test_delete_keyword_returns_removal_reply"
  - "tests/test_agent.py::TestLocalSimulation::test_list_keyword_returns_listing_reply"
  - "tests/test_agent.py::TestLocalSimulation::test_hello_keyword_returns_greeting"
  - "tests/test_agent.py::TestLocalSimulation::test_hi_keyword_returns_greeting"
  - "tests/test_agent.py::TestLocalSimulation::test_unknown_message_returns_preview_mode_notice"
  - "tests/test_agent.py::TestLocalSimulation::test_matching_is_case_insensitive"
  - "tests/test_agent.py::TestLocalSimulation::test_call_llm_uses_simulation_when_no_api_key"
  - "tests/test_agent.py::TestLocalSimulation::test_call_llm_simulation_does_not_raise_503"
---

## Prompt

Refactor Chat Safe Mode to simulate AI responses without OpenAI API.

Requirements:
- When OPENAI_API_KEY is missing, DO NOT return "You said:"
- Implement local AI simulation logic inside TaskAgent fallback.
- Generate contextual responses based on message content.

Rules:
- If message contains "add" → reply "Sure, I can help add that task."
- "delete" → "Okay, removing that task."
- "list" → "Here are your current tasks."
- "hello" or "hi" → friendly greeting
- Otherwise: reply "I'm in preview mode. AI backend will be connected in Phase III."

Do NOT change routes. Do NOT change auth. Only update agent fallback logic.

## Response

### backend/agents/agent.py (2 changes)

1. Added `_local_simulate(self, messages)` method with keyword-based matching (case-insensitive):
   - Scans first user-role message for intent keywords (add / delete / list / hello / hi)
   - Returns a contextual `LLMMessage(content=..., stop_reason="stop")` with no tool_calls
   - Default branch returns preview-mode notice for unrecognised input

2. Changed `_call_llm` no-key branch:
   ```python
   if not api_key:
       return self._local_simulate(messages)  # was: raise HTTPException(503)
   ```
   - No longer raises 503; always returns a useful contextual reply
   - `_local_simulate` is synchronous; `_call_llm` returns it directly (no await needed)

### backend/tests/test_agent.py (new class TestLocalSimulation, 9 tests)

- `test_add_keyword_returns_task_creation_reply`: "add" keyword → creation reply
- `test_delete_keyword_returns_removal_reply`: "delete" keyword → removal reply
- `test_list_keyword_returns_listing_reply`: "list" keyword → listing reply
- `test_hello_keyword_returns_greeting`: "hello" → greeting
- `test_hi_keyword_returns_greeting`: "hi!" → same greeting
- `test_unknown_message_returns_preview_mode_notice`: unrecognised → preview notice
- `test_matching_is_case_insensitive`: "ADD" matches same as "add"
- `test_call_llm_uses_simulation_when_no_api_key`: `_call_llm` delegates to `_local_simulate` when env var absent
- `test_call_llm_simulation_does_not_raise_503`: no HTTPException raised without key

## Outcome

- [x] `_local_simulate` method added to `TaskAgent` with 5 keyword branches
- [x] `_call_llm` no-key path calls `_local_simulate` instead of raising 503
- [x] Routes, auth, and safe-mode try/except unchanged
- [x] 9 new `TestLocalSimulation` tests — all pass
- [x] 45/45 agent tests pass
- [x] 203/203 total tests pass (zero regressions)
