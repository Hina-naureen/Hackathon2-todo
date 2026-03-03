# agents/base.py — BaseAgent ABC + shared dataclasses
# References: specs/agents/agent-behavior.md §LLM Interface
#             specs/agents/agent-behavior.md §Agentic Loop
#             specs/agents/agent-behavior.md §ActionTrace Type

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Literal

from sqlmodel import Session

# ---------------------------------------------------------------------------
# Shared LLM types — SDK-agnostic; cross the boundary between the agentic
# loop and any LLM backend (OpenAI, Claude, local simulation).
# ---------------------------------------------------------------------------


@dataclass
class LLMToolCall:
    """One tool invocation requested by the LLM."""

    id: str               # tool_call_id — echoed back in tool result
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


@dataclass
class ActionTrace:
    """Recorded for every call_tool() invocation within one request."""

    tool: str             # e.g. "create_task"
    args: dict[str, Any]  # e.g. {"title": "Buy milk"}
    result: Any           # e.g. {"id": 5, "title": "Buy milk", "completed": false}


# ---------------------------------------------------------------------------
# BaseAgent — shared agentic loop, subclassed by OpenAITaskAgent & ClaudeTaskAgent
# References: specs/agents/agent-behavior.md §Agentic Loop
# ---------------------------------------------------------------------------

_MAX_ITERATIONS = 5  # safety cap; prevents runaway tool-call loops


class BaseAgent(ABC):
    """Abstract base for all task agents.

    Subclasses must implement:
        _call_llm(messages)   — call the LLM and return LLMMessage
        _call_tool(name, args) — execute a named tool and return result
        _get_system_prompt()  — return the system prompt string

    The shared `run()` loop is defined here; it calls these abstract methods.
    """

    def __init__(self, session: Session, user_id: str) -> None:
        """Initialise agent with a DB session and authenticated user ID."""
        self._session = session
        self._user_id = user_id
        self.pending_task: dict | None = None  # populated during dry_run

    @abstractmethod
    async def _call_llm(self, messages: list[dict]) -> LLMMessage:
        """Call the LLM backend and return a normalised LLMMessage."""
        ...

    @abstractmethod
    def _call_tool(self, name: str, args: dict[str, Any]) -> Any:
        """Execute the named tool with the given args and return the result."""
        ...

    @abstractmethod
    def _get_system_prompt(self) -> str:
        """Return the system prompt string for this agent."""
        ...

    # ------------------------------------------------------------------
    # Shared agentic loop
    # References: specs/agents/agent-behavior.md §Agentic Loop
    # ------------------------------------------------------------------

    async def run(
        self, user_message: str, today: str | None = None, dry_run: bool = False
    ) -> tuple[str, list[ActionTrace]]:
        """Execute the agentic loop for one user message.

        today — optional YYYY-MM-DD string from the client. When provided it is
        prepended to the user message so the LLM can resolve relative date
        phrases ("tomorrow", "next Friday") correctly.

        Returns (reply_text, actions) where actions lists every tool invoked.
        """
        context_note = f"[Today is {today}] " if today else ""
        messages: list[dict] = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": context_note + user_message},
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
                # dry_run: intercept create_task — extract data without persisting
                if dry_run and tc.name == "create_task":
                    self.pending_task = tc.args
                    title = tc.args.get("title", "task")
                    due = tc.args.get("due_date")
                    due_str = f" due {due[:10]}" if due else ""
                    return (
                        f'Ready to create "{title}"{due_str}. '
                        "Click the button below to add it to your list.",
                        actions,
                    )

                result = self._call_tool(tc.name, tc.args)
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
