# agents/agent.py — TaskAgent: agentic loop with OpenAI function calling
# References: specs/agents/agent-behavior.md
#             specs/api/mcp-tools.md §Tool Dispatch

from __future__ import annotations

import json
import os
import re
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
        """Rule-based simulation used when OPENAI_API_KEY is not configured.

        Pass 1 (no tool results yet): parse user intent → return tool_calls so
        the agentic loop executes the real tools and persists to the database.
        Pass 2 (tool results present): generate a friendly human-readable reply.
        """
        # ── Pass 2: tool results already in context → generate reply ──────
        tool_msgs = [m for m in messages if m.get("role") == "tool"]
        if tool_msgs:
            tool_name = ""
            for m in reversed(messages):
                if m.get("role") == "assistant" and m.get("tool_calls"):
                    tool_name = m["tool_calls"][-1]["function"]["name"]
                    break

            result = json.loads(tool_msgs[-1]["content"])

            if "error" in result:
                return LLMMessage(
                    content=f"Sorry, I couldn't do that: {result['error']}",
                    stop_reason="stop",
                )

            if tool_name == "create_task":
                title = result.get("title", "task")
                due = result.get("due_date")
                suffix = f" due {due[:10]}" if due else ""
                return LLMMessage(
                    content=f'Done! Created task "{title}"{suffix}.',
                    stop_reason="stop",
                )

            if tool_name == "list_tasks":
                tasks = result.get("tasks", [])
                if not tasks:
                    return LLMMessage(
                        content="You have no tasks yet. Try: 'add buy milk'.",
                        stop_reason="stop",
                    )
                lines = []
                for t in tasks:
                    status = "✓" if t["completed"] else "○"
                    due = f" (due {t['due_date'][:10]})" if t.get("due_date") else ""
                    lines.append(f"{status} [{t['id']}] {t['title']}{due}")
                return LLMMessage(
                    content="Here are your tasks:\n" + "\n".join(lines),
                    stop_reason="stop",
                )

            if tool_name == "delete_task":
                title = result.get("title", "")
                label = f' "{title}"' if title else ""
                return LLMMessage(
                    content=f"Deleted task{label}.", stop_reason="stop"
                )

            if tool_name == "toggle_complete":
                title = result.get("title", "task")
                state = "completed ✓" if result.get("completed") else "marked as pending"
                return LLMMessage(
                    content=f'"{title}" {state}.', stop_reason="stop"
                )

            if tool_name == "update_task":
                title = result.get("title", "task")
                return LLMMessage(
                    content=f'Updated task "{title}".', stop_reason="stop"
                )

            return LLMMessage(content="Done!", stop_reason="stop")

        # ── Pass 1: parse user intent → return tool_calls ─────────────────
        user_text = ""
        today: str | None = None
        for m in messages:
            if m.get("role") == "user":
                raw = m.get("content") or ""
                date_match = re.match(
                    r"\[Today is (\d{4}-\d{2}-\d{2})\]\s*(.*)", raw, re.DOTALL
                )
                if date_match:
                    today = date_match.group(1)
                    user_text = date_match.group(2)
                else:
                    user_text = raw
                break

        lower = user_text.lower()

        # ── list / show tasks ──────────────────────────────────────────────
        is_list = bool(
            re.search(r"\b(list|show|display|view|see)\b", lower)
            and not re.search(r"\b(add|create|make|new)\b", lower)
        )
        is_list = is_list or bool(re.search(r"\bmy tasks\b", lower))
        if is_list:
            filt = (
                "pending"
                if re.search(r"\b(pending|incomplete|remaining)\b", lower)
                else "completed"
                if re.search(r"\b(completed|done|finished)\b", lower)
                else "all"
            )
            return LLMMessage(
                content=None,
                stop_reason="tool_calls",
                tool_calls=[
                    LLMToolCall(id="sim_1", name="list_tasks", args={"filter": filt})
                ],
            )

        # ── delete task ────────────────────────────────────────────────────
        if re.search(r"\b(delete|remove|erase|drop)\b", lower):
            id_match = re.search(r"\b(\d+)\b", lower)
            if id_match:
                return LLMMessage(
                    content=None,
                    stop_reason="tool_calls",
                    tool_calls=[
                        LLMToolCall(
                            id="sim_1",
                            name="delete_task",
                            args={"id": int(id_match.group(1))},
                        )
                    ],
                )
            return LLMMessage(
                content="Which task number should I delete? (e.g. 'delete task 3')",
                stop_reason="stop",
            )

        # ── toggle / complete ──────────────────────────────────────────────
        if re.search(r"\b(complete|finish|done|toggle|mark|check)\b", lower):
            id_match = re.search(r"\b(\d+)\b", lower)
            if id_match:
                return LLMMessage(
                    content=None,
                    stop_reason="tool_calls",
                    tool_calls=[
                        LLMToolCall(
                            id="sim_1",
                            name="toggle_complete",
                            args={"id": int(id_match.group(1))},
                        )
                    ],
                )
            return LLMMessage(
                content="Which task number should I mark as done? (e.g. 'complete task 2')",
                stop_reason="stop",
            )

        # ── add / create task ──────────────────────────────────────────────
        if re.search(r"\b(add|create|new|make|set|remind)\b", lower) or re.search(
            r"\btask\b", lower
        ):
            # Strip command words to extract the title
            title = re.sub(
                r"\b(add|create|new|make|set|remind|me|to|a|an|the|task|todo|reminder)\b",
                "",
                lower,
                flags=re.IGNORECASE,
            ).strip()

            # Extract due_date from natural language
            due_date: str | None = None
            if today:
                from datetime import date, timedelta  # noqa: PLC0415

                td = date.fromisoformat(today)
                if re.search(r"\btomorrow\b", lower):
                    due_date = (td + timedelta(days=1)).isoformat() + "T09:00:00"
                    title = re.sub(
                        r"\btomorrow\b", "", title, flags=re.IGNORECASE
                    ).strip()
                elif re.search(r"\btoday\b", lower):
                    due_date = td.isoformat() + "T09:00:00"
                    title = re.sub(
                        r"\btoday\b", "", title, flags=re.IGNORECASE
                    ).strip()

                # Extract explicit time "at 2 PM" / "at 14:00"
                time_match = re.search(
                    r"\bat\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b", lower
                )
                if time_match and due_date:
                    h = int(time_match.group(1))
                    mins = int(time_match.group(2) or 0)
                    ampm = time_match.group(3)
                    if ampm == "pm" and h < 12:
                        h += 12
                    elif ampm == "am" and h == 12:
                        h = 0
                    due_date = due_date[:10] + f"T{h:02d}:{mins:02d}:00"
                    title = re.sub(
                        r"\bat\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?\b",
                        "",
                        title,
                        flags=re.IGNORECASE,
                    ).strip()

            title = re.sub(r"\s+", " ", title).strip() or "New Task"
            title = title[0].upper() + title[1:]

            args: dict = {"title": title}
            if due_date:
                args["due_date"] = due_date

            return LLMMessage(
                content=None,
                stop_reason="tool_calls",
                tool_calls=[LLMToolCall(id="sim_1", name="create_task", args=args)],
            )

        # ── greeting ───────────────────────────────────────────────────────
        if re.search(r"\b(hello|hi|hey|salam|salaam|assalam)\b", lower):
            return LLMMessage(
                content=(
                    "Hello! I can help you manage your tasks. Try:\n"
                    "• 'add buy groceries'\n"
                    "• 'add meeting tomorrow at 2 PM'\n"
                    "• 'show my tasks'\n"
                    "• 'complete task 3'\n"
                    "• 'delete task 5'"
                ),
                stop_reason="stop",
            )

        # ── fallback ───────────────────────────────────────────────────────
        return LLMMessage(
            content=(
                "I can help you manage tasks. Try:\n"
                "• 'add buy milk'\n"
                "• 'add meeting tomorrow at 2 PM'\n"
                "• 'list my tasks'\n"
                "• 'complete task 3'\n"
                "• 'delete task 5'"
            ),
            stop_reason="stop",
        )

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

    async def run(
        self, user_message: str, today: str | None = None
    ) -> tuple[str, list[ActionTrace]]:
        """Execute the agentic loop for one user message.

        today — optional YYYY-MM-DD string from the client. When provided it is
        prepended to the user message so the LLM can resolve relative date
        phrases ("tomorrow", "next Friday") correctly.

        Returns (reply_text, actions) where actions lists every tool invoked.
        """
        # Inject today's date into the context when provided.
        context_note = f"[Today is {today}] " if today else ""
        messages: list[dict] = [
            {"role": "system", "content": SYSTEM_PROMPT},
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
