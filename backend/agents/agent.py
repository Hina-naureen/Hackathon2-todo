# agents/agent.py — TaskAgent: agentic loop with OpenAI function calling
# References: specs/agents/agent-behavior.md
#             specs/api/mcp-tools.md §Tool Dispatch

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Literal

from fastapi import HTTPException
from sqlmodel import Session

from agents.prompts import SYSTEM_PROMPT
from agents.tools import TOOL_SCHEMAS, call_tool

# ---------------------------------------------------------------------------
# Internal LLM types — independent of the OpenAI SDK
# These are the only types that cross the boundary between the agentic loop
# and the LLM backend. Keeping them SDK-agnostic makes _call_llm easy to
# monkeypatch in tests.
# References: specs/agents/agent-behavior.md §LLM Interface
# ---------------------------------------------------------------------------


@dataclass
class LLMToolCall:
    """One tool invocation requested by the LLM."""

    id: str               # OpenAI tool_call_id — echoed back in tool result
    name: str             # Tool function name, e.g. "create_task"
    args: dict[str, Any]  # Parsed JSON arguments


@dataclass
class LLMMessage:
    """Normalised response from _call_llm.

    When stop_reason == "stop"       → content holds the final reply text.
    When stop_reason == "tool_calls" → tool_calls is non-empty; content is None.
    """

    content: str | None
    stop_reason: Literal["stop", "tool_calls"]
    tool_calls: list[LLMToolCall] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Action trace — one entry per tool invoked during the request
# References: specs/agents/agent-behavior.md §ActionTrace Type
# ---------------------------------------------------------------------------


@dataclass
class ActionTrace:
    """Recorded for every call_tool() invocation within one request."""

    tool: str             # e.g. "create_task"
    args: dict[str, Any]  # e.g. {"title": "Buy milk"}
    result: Any           # e.g. {"id": 5, "title": "Buy milk", "completed": false}


# ---------------------------------------------------------------------------
# Agent
# References: specs/agents/agent-behavior.md §Agentic Loop
# ---------------------------------------------------------------------------

_MAX_ITERATIONS = 5  # safety cap; prevents runaway tool-call loops


class TaskAgent:
    """Stateless agentic loop: user message → LLM → (tool calls)* → reply.

    Instantiate once per request. `_call_llm` is the only method that touches
    the external AI service — monkeypatch it in tests to avoid real API calls.

    References: specs/agents/agent-behavior.md
    """

    def __init__(self, session: Session, user_id: str) -> None:
        self._session = session
        self._user_id = user_id

    # ------------------------------------------------------------------
    # LLM interface — thin wrapper around OpenAI; mockable in tests
    # References: specs/agents/agent-behavior.md §LLM Interface (_call_llm)
    # ------------------------------------------------------------------

    def _local_simulate(self, messages: list[dict]) -> LLMMessage:
        """Keyword-based simulation used when OPENAI_API_KEY is not configured.

        Scans the first user-role message for intent keywords and returns a
        contextual reply with no external API call.

        Rules (checked in order, case-insensitive):
          "add"           → task-creation acknowledgement
          "delete"        → task-removal acknowledgement
          "list"          → task-listing acknowledgement
          "hello"/"hi"    → friendly greeting
          (anything else) → preview-mode notice
        """
        user_text = ""
        for m in messages:
            if m.get("role") == "user":
                user_text = (m.get("content") or "").lower()
                break

        if "add" in user_text:
            reply = "Sure, I can help add that task."
        elif "delete" in user_text:
            reply = "Okay, removing that task."
        elif "list" in user_text:
            reply = "Here are your current tasks."
        elif "hello" in user_text or "hi" in user_text:
            reply = "Hello! How can I help you manage your tasks today?"
        else:
            reply = "I'm in preview mode. AI backend will be connected in Phase III."

        return LLMMessage(content=reply, stop_reason="stop")

    async def _call_llm(self, messages: list[dict]) -> LLMMessage:
        """Call OpenAI chat completions and return a normalised LLMMessage.

        Falls back to _local_simulate when OPENAI_API_KEY is not set.
        Raises HTTP 503 only if the openai package is not installed.
        Monkeypatch this method on agent instances in tests.
        """
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return self._local_simulate(messages)

        try:
            import openai  # noqa: PLC0415
        except ImportError as exc:
            raise HTTPException(
                status_code=503,
                detail="openai package not installed.",
            ) from exc

        client = openai.AsyncOpenAI(api_key=api_key)
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
        )

        msg = response.choices[0].message
        if msg.tool_calls:
            return LLMMessage(
                content=None,
                stop_reason="tool_calls",
                tool_calls=[
                    LLMToolCall(
                        id=tc.id,
                        name=tc.function.name,
                        args=json.loads(tc.function.arguments),
                    )
                    for tc in msg.tool_calls
                ],
            )
        return LLMMessage(
            content=msg.content or "",
            stop_reason="stop",
        )

    # ------------------------------------------------------------------
    # Agentic loop
    # References: specs/agents/agent-behavior.md §Agentic Loop
    # ------------------------------------------------------------------

    async def run(self, user_message: str) -> tuple[str, list[ActionTrace]]:
        """Execute the agentic loop for one user message.

        Returns (reply_text, actions) where actions lists every tool invoked.
        """
        messages: list[dict] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]
        actions: list[ActionTrace] = []

        for _ in range(_MAX_ITERATIONS):
            llm_msg = await self._call_llm(messages)

            if llm_msg.stop_reason == "stop":
                return llm_msg.content or "", actions

            # Build the assistant turn with tool_calls for the next LLM call
            assistant_tool_calls = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.name,
                        "arguments": json.dumps(tc.args),
                    },
                }
                for tc in llm_msg.tool_calls
            ]
            messages.append(
                {"role": "assistant", "content": None, "tool_calls": assistant_tool_calls}
            )

            # Execute each tool, record the trace, append the tool result
            for tc in llm_msg.tool_calls:
                result = call_tool(self._session, self._user_id, tc.name, tc.args)
                actions.append(ActionTrace(tool=tc.name, args=tc.args, result=result))
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(result),
                    }
                )

        # Safety fallback — loop exhausted
        return "I'm having trouble completing that request. Please try again.", actions
