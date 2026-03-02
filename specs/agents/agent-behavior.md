# Agent Behavior Specification: TaskAgent — Phase III

**Version:** 1.1.0
**Date:** 2026-03-02
**Status:** Implemented
**Stage:** green
**Phase:** III
**References:**
- `specs/features/chatbot.md` — feature requirements
- `specs/api/mcp-tools.md` — tool contracts
- `specs/api/chat-endpoint.md` — HTTP contract

---

## Overview

`TaskAgent` is a stateless Python class that wraps OpenAI function calling into
an agentic loop. It receives a single user message per request, may call tools
zero or more times, and returns a natural-language reply plus an `actions` trace.

Each request is fully independent — there is no conversation memory between
requests. The agent is instantiated per request inside the `/api/chat` route
handler and discarded after returning.

---

## Agentic Loop

```
User message
    │
    ▼
┌──────────────────────────────────────────────────────┐
│                   Iteration (max 5)                  │
│                                                      │
│   messages ──► _call_llm(messages)                   │
│                      │                               │
│           ┌──────────┴──────────┐                    │
│     stop_reason="stop"   stop_reason="tool_calls"    │
│           │                     │                    │
│       RETURN reply          for each tool_call:      │
│                               call_tool(...)         │
│                               append tool result     │
│                               to messages            │
│                               (loop continues)       │
└──────────────────────────────────────────────────────┘
    │
    ▼
Safety fallback reply (if max iterations reached)
```

**Invariants:**
- `messages` always starts with the system prompt + user message.
- After each tool-call turn, the assistant's tool_calls message AND each tool
  result are appended before the next LLM call.
- The loop terminates immediately when `stop_reason == "stop"`.

---

## LLM Interface (`_call_llm`)

`_call_llm(messages: list[dict]) -> LLMMessage` is the only point of contact
with the external AI service. It is an async instance method.

**Design rationale:** Keeping the LLM interaction in a single method enables
clean monkeypatching in tests without importing the `openai` SDK. The rest of
the agent logic is fully deterministic and testable in isolation.

**Production behavior:**
- Uses `openai.AsyncOpenAI` with model `gpt-4o-mini`.
- Passes `TOOL_SCHEMAS` and `tool_choice="auto"`.
- Falls back to `_local_simulate()` if `OPENAI_API_KEY` is not set (no 503 — app stays live).
- Raises `HTTP 503` only if the `openai` package is not installed at all.

**Test behavior:**
- Monkeypatched via `monkeypatch.setattr(agent_instance, "_call_llm", fake_fn)`.
- `fake_fn(messages: list[dict]) -> LLMMessage` returns predetermined responses.

---

## LLMMessage Type

```python
@dataclass
class LLMMessage:
    content: str | None            # Final text reply (set when stop_reason="stop")
    stop_reason: Literal["stop", "tool_calls"]
    tool_calls: list[LLMToolCall]  # Non-empty when stop_reason="tool_calls"

@dataclass
class LLMToolCall:
    id: str              # OpenAI tool_call_id (used in tool result message)
    name: str            # Tool function name
    args: dict[str, Any] # Parsed JSON arguments
```

---

## ActionTrace Type

Every tool invocation is recorded as an `ActionTrace` and returned in the
`actions` field of the HTTP response:

```python
@dataclass
class ActionTrace:
    tool: str            # e.g., "create_task"
    args: dict[str, Any] # e.g., {"title": "Buy milk"}
    result: Any          # e.g., {"id": 5, "title": "Buy milk", "completed": false}
```

`actions` is empty (`[]`) when the agent answers without calling any tool
(e.g., an off-topic question or a direct factual answer).

---

## System Prompt Rules

The system prompt (in `agents/prompts.py`) establishes the following constraints
for the LLM:

1. **Tool-only data access:** Use tools for all reads and writes. Never invent task data.
2. **Mandatory tool use:** Always invoke a tool when the user's intent involves
   creating, listing, updating, or toggling tasks.
3. **Off-topic redirect:** Politely decline non-task questions; suggest what can
   be done instead.
4. **Confirmation replies:** After tool calls, confirm what was done and include
   the task title and/or ID.
5. **Multi-tool sequencing:** Multiple tools may be called in sequence within
   one request if needed (e.g., list then toggle).

---

## Safety Constraints

| Constraint | Implementation |
|------------|---------------|
| Max iterations | `_MAX_ITERATIONS = 5` — loop exits after 5 LLM calls |
| User scoping | `user_id` is injected into every `call_tool(session, user_id, ...)` call |
| Tool errors in-band | Tool errors are returned as `{"error": "..."}` dicts, not exceptions |
| Fallback reply | If loop exhausts, return `"I'm having trouble completing that request."` |
| No direct DB access | Agent only mutates state through `call_tool` |

---

## Request Lifecycle

```
POST /api/chat
    │
    ├─ validate message (400 if empty)
    ├─ get_current_user → user_id           (JWT dep)
    ├─ get_session → session                (DB dep)
    ├─ TaskAgent(session, user_id).run(msg)
    │       └─ agentic loop (above)
    └─ return ChatResponse(reply, trace_id, actions)
```

---

## Error Handling

| Scenario | Outcome |
|----------|---------|
| `OPENAI_API_KEY` not set | Falls back to `_local_simulate()` — HTTP 200 with canned keyword reply; no 503 |
| `openai` package not installed | `HTTP 503 {"detail": "openai package not installed."}` |
| Tool returns `{"error": ...}` | Agent sees the error in its tool result, communicates it in the reply; HTTP 200 |
| Max iterations reached | HTTP 200 with fallback reply; `actions` contains all tools called so far |
| JWT missing/invalid | `HTTP 401` (handled before agent is instantiated) |
| Empty message | `HTTP 400` (handled before agent is instantiated) |

---

## File Locations

| File | Purpose |
|------|---------|
| `backend/agents/agent.py` | `LLMMessage`, `LLMToolCall`, `ActionTrace`, `TaskAgent` |
| `backend/agents/tools.py` | Tool functions, `TOOL_REGISTRY`, `call_tool`, `TOOL_SCHEMAS` |
| `backend/agents/prompts.py` | `SYSTEM_PROMPT` |
| `backend/src/routes/chat.py` | HTTP route that instantiates and runs the agent |
| `backend/tests/test_agent.py` | Unit tests for agent loop and tool calling |

---

## References

| Document | Path |
|----------|------|
| Feature spec | `specs/features/chatbot.md` |
| Tool contracts | `specs/api/mcp-tools.md` |
| HTTP contract | `specs/api/chat-endpoint.md` |
| Auth spec | `specs/features/authentication.md` |
