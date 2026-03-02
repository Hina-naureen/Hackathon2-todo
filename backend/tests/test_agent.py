# tests/test_agent.py — Unit tests for TaskAgent agentic loop and tools
# References: specs/agents/agent-behavior.md
#             specs/api/mcp-tools.md §Tool Definitions
#             specs/features/chatbot.md §Acceptance Criteria
#             agents/agent.py §_local_simulate
#
# All tests monkeypatch TaskAgent._call_llm on the agent instance so no
# OPENAI_API_KEY is needed. Tool functions use a real in-memory SQLite DB.

from __future__ import annotations

import asyncio
from typing import Any

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from agents.agent import ActionTrace, LLMMessage, LLMToolCall, TaskAgent
from agents.tools import call_tool, create_task, list_tasks, toggle_complete, update_task
from src.db_models import Task

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TEST_USER = "agent-test-user"
OTHER_USER = "agent-other-user"


def _run(coro) -> Any:
    """Run an async coroutine in a blocking context for synchronous pytest tests."""
    return asyncio.run(coro)


@pytest.fixture(name="session")
def session_fixture():
    """Fresh in-memory SQLite session per test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


def _seed_task(session: Session, title: str, user_id: str = TEST_USER) -> Task:
    """Insert a task directly into the DB and return it."""
    task = Task(title=title, user_id=user_id)
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


# ---------------------------------------------------------------------------
# Tool function unit tests
# References: specs/api/mcp-tools.md §Tool Definitions
# ---------------------------------------------------------------------------


class TestCreateTaskTool:
    def test_creates_task_and_returns_id(self, session: Session):
        result = create_task(session, TEST_USER, "Buy milk")
        assert result["id"] is not None
        assert result["title"] == "Buy milk"
        assert result["completed"] is False

    def test_description_defaults_to_empty(self, session: Session):
        result = create_task(session, TEST_USER, "No desc")
        assert result["description"] == ""

    def test_description_stored(self, session: Session):
        result = create_task(session, TEST_USER, "Task", "Some details")
        assert result["description"] == "Some details"

    def test_empty_title_returns_error(self, session: Session):
        result = create_task(session, TEST_USER, "")
        assert "error" in result
        assert "empty" in result["error"].lower()

    def test_whitespace_title_returns_error(self, session: Session):
        result = create_task(session, TEST_USER, "   ")
        assert "error" in result

    def test_title_too_long_returns_error(self, session: Session):
        result = create_task(session, TEST_USER, "x" * 201)
        assert "error" in result
        assert "200" in result["error"]

    def test_description_too_long_returns_error(self, session: Session):
        result = create_task(session, TEST_USER, "ok", "x" * 501)
        assert "error" in result
        assert "500" in result["error"]

    def test_title_stripped_before_storage(self, session: Session):
        result = create_task(session, TEST_USER, "  spaced  ")
        assert result["title"] == "spaced"


class TestListTasksTool:
    def test_returns_all_tasks(self, session: Session):
        _seed_task(session, "A")
        _seed_task(session, "B")
        result = list_tasks(session, TEST_USER)
        assert result["count"] == 2
        titles = [t["title"] for t in result["tasks"]]
        assert "A" in titles and "B" in titles

    def test_empty_list(self, session: Session):
        result = list_tasks(session, TEST_USER)
        assert result["count"] == 0
        assert result["tasks"] == []

    def test_filter_pending(self, session: Session):
        t1 = _seed_task(session, "Pending")
        t2 = _seed_task(session, "Done")
        t2.completed = True
        session.commit()

        result = list_tasks(session, TEST_USER, filter="pending")
        assert result["count"] == 1
        assert result["tasks"][0]["title"] == "Pending"

    def test_filter_completed(self, session: Session):
        _seed_task(session, "Pending")
        t2 = _seed_task(session, "Done")
        t2.completed = True
        session.commit()

        result = list_tasks(session, TEST_USER, filter="completed")
        assert result["count"] == 1
        assert result["tasks"][0]["title"] == "Done"

    def test_does_not_return_other_users_tasks(self, session: Session):
        _seed_task(session, "Mine", user_id=TEST_USER)
        _seed_task(session, "Theirs", user_id=OTHER_USER)

        result = list_tasks(session, TEST_USER)
        titles = [t["title"] for t in result["tasks"]]
        assert "Mine" in titles
        assert "Theirs" not in titles


class TestUpdateTaskTool:
    def test_updates_title(self, session: Session):
        task = _seed_task(session, "Old title")
        result = update_task(session, TEST_USER, task.id, title="New title")
        assert result["title"] == "New title"

    def test_null_title_keeps_existing(self, session: Session):
        task = _seed_task(session, "Keep me")
        result = update_task(session, TEST_USER, task.id, title=None)
        assert result["title"] == "Keep me"

    def test_updates_description(self, session: Session):
        task = _seed_task(session, "Task")
        result = update_task(session, TEST_USER, task.id, description="New desc")
        assert result["description"] == "New desc"

    def test_nonexistent_task_returns_error(self, session: Session):
        result = update_task(session, TEST_USER, 9999, title="Ghost")
        assert "error" in result
        assert "not found" in result["error"].lower()

    def test_empty_title_returns_error(self, session: Session):
        task = _seed_task(session, "Task")
        result = update_task(session, TEST_USER, task.id, title="")
        assert "error" in result

    def test_other_users_task_not_updated(self, session: Session):
        other_task = _seed_task(session, "Private", user_id=OTHER_USER)
        result = update_task(session, TEST_USER, other_task.id, title="Hijacked")
        assert "error" in result


class TestToggleCompleteTool:
    def test_pending_becomes_completed(self, session: Session):
        task = _seed_task(session, "Todo")
        result = toggle_complete(session, TEST_USER, task.id)
        assert result["completed"] is True

    def test_completed_becomes_pending(self, session: Session):
        task = _seed_task(session, "Done")
        task.completed = True
        session.commit()

        result = toggle_complete(session, TEST_USER, task.id)
        assert result["completed"] is False

    def test_nonexistent_task_returns_error(self, session: Session):
        result = toggle_complete(session, TEST_USER, 9999)
        assert "error" in result
        assert "not found" in result["error"].lower()

    def test_other_users_task_not_toggled(self, session: Session):
        other_task = _seed_task(session, "Private", user_id=OTHER_USER)
        result = toggle_complete(session, TEST_USER, other_task.id)
        assert "error" in result


class TestCallToolDispatch:
    def test_unknown_tool_returns_error(self, session: Session):
        result = call_tool(session, TEST_USER, "delete_everything", {})
        assert "error" in result
        assert "Unknown tool" in result["error"]

    def test_dispatches_create_task(self, session: Session):
        result = call_tool(session, TEST_USER, "create_task", {"title": "Via dispatch"})
        assert result["title"] == "Via dispatch"

    def test_user_id_cannot_be_overridden_via_args(self, session: Session):
        """user_id comes from the injected parameter, never from tool args."""
        _seed_task(session, "Private", user_id=OTHER_USER)
        # Even if an attacker passes other user's task id, scoping prevents access
        result = call_tool(session, TEST_USER, "list_tasks", {"filter": "all"})
        titles = [t["title"] for t in result["tasks"]]
        assert "Private" not in titles


# ---------------------------------------------------------------------------
# Agent agentic loop tests
# References: specs/agents/agent-behavior.md §Agentic Loop
# ---------------------------------------------------------------------------


class TestAgentLoop:
    def test_no_tool_calls_returns_reply_and_empty_actions(
        self, session: Session, monkeypatch: pytest.MonkeyPatch
    ):
        agent = TaskAgent(session, TEST_USER)

        async def fake_llm(messages):
            return LLMMessage(content="Hello! How can I help?", stop_reason="stop")

        monkeypatch.setattr(agent, "_call_llm", fake_llm)

        reply, actions = _run(agent.run("Hi"))
        assert reply == "Hello! How can I help?"
        assert actions == []

    def test_create_task_via_tool_call(
        self, session: Session, monkeypatch: pytest.MonkeyPatch
    ):
        # References: specs/features/chatbot.md §US-CHAT-01
        agent = TaskAgent(session, TEST_USER)
        call_count = 0

        async def fake_llm(messages):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return LLMMessage(
                    content=None,
                    stop_reason="tool_calls",
                    tool_calls=[
                        LLMToolCall(id="tc1", name="create_task", args={"title": "Buy milk"})
                    ],
                )
            return LLMMessage(content="Created task 'Buy milk'!", stop_reason="stop")

        monkeypatch.setattr(agent, "_call_llm", fake_llm)

        reply, actions = _run(agent.run("Add a task to buy milk"))

        assert len(actions) == 1
        assert actions[0].tool == "create_task"
        assert actions[0].args == {"title": "Buy milk"}
        assert "id" in actions[0].result       # task was actually inserted
        assert actions[0].result["title"] == "Buy milk"
        assert "Buy milk" in reply

    def test_list_tasks_via_tool_call(
        self, session: Session, monkeypatch: pytest.MonkeyPatch
    ):
        # References: specs/features/chatbot.md §US-CHAT-02
        _seed_task(session, "Exercise")
        agent = TaskAgent(session, TEST_USER)
        call_count = 0

        async def fake_llm(messages):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return LLMMessage(
                    content=None,
                    stop_reason="tool_calls",
                    tool_calls=[
                        LLMToolCall(id="tc1", name="list_tasks", args={"filter": "all"})
                    ],
                )
            return LLMMessage(content="You have 1 task: Exercise.", stop_reason="stop")

        monkeypatch.setattr(agent, "_call_llm", fake_llm)

        reply, actions = _run(agent.run("What tasks do I have?"))

        assert actions[0].tool == "list_tasks"
        assert actions[0].result["count"] == 1
        assert actions[0].result["tasks"][0]["title"] == "Exercise"
        assert "Exercise" in reply

    def test_toggle_complete_via_tool_call(
        self, session: Session, monkeypatch: pytest.MonkeyPatch
    ):
        # References: specs/features/chatbot.md §US-CHAT-03
        task = _seed_task(session, "Submit report")
        agent = TaskAgent(session, TEST_USER)
        call_count = 0

        async def fake_llm(messages):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return LLMMessage(
                    content=None,
                    stop_reason="tool_calls",
                    tool_calls=[
                        LLMToolCall(
                            id="tc1",
                            name="toggle_complete",
                            args={"id": task.id},
                        )
                    ],
                )
            return LLMMessage(
                content=f"Marked task #{task.id} as complete!", stop_reason="stop"
            )

        monkeypatch.setattr(agent, "_call_llm", fake_llm)

        reply, actions = _run(agent.run(f"Mark task {task.id} as done"))

        assert actions[0].tool == "toggle_complete"
        assert actions[0].result["completed"] is True

    def test_update_task_via_tool_call(
        self, session: Session, monkeypatch: pytest.MonkeyPatch
    ):
        # References: specs/features/chatbot.md §US-CHAT-04
        task = _seed_task(session, "Buy milk")
        agent = TaskAgent(session, TEST_USER)
        call_count = 0

        async def fake_llm(messages):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return LLMMessage(
                    content=None,
                    stop_reason="tool_calls",
                    tool_calls=[
                        LLMToolCall(
                            id="tc1",
                            name="update_task",
                            args={"id": task.id, "title": "Buy organic milk"},
                        )
                    ],
                )
            return LLMMessage(content="Updated to 'Buy organic milk'.", stop_reason="stop")

        monkeypatch.setattr(agent, "_call_llm", fake_llm)

        reply, actions = _run(agent.run("Rename the milk task"))

        assert actions[0].tool == "update_task"
        assert actions[0].result["title"] == "Buy organic milk"

    def test_multiple_tool_calls_in_sequence(
        self, session: Session, monkeypatch: pytest.MonkeyPatch
    ):
        """Agent calls two tools across two loop iterations."""
        agent = TaskAgent(session, TEST_USER)
        call_count = 0

        async def fake_llm(messages):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return LLMMessage(
                    content=None,
                    stop_reason="tool_calls",
                    tool_calls=[
                        LLMToolCall(id="tc1", name="create_task", args={"title": "Task A"})
                    ],
                )
            if call_count == 2:
                return LLMMessage(
                    content=None,
                    stop_reason="tool_calls",
                    tool_calls=[
                        LLMToolCall(id="tc2", name="create_task", args={"title": "Task B"})
                    ],
                )
            return LLMMessage(content="Created Task A and Task B.", stop_reason="stop")

        monkeypatch.setattr(agent, "_call_llm", fake_llm)

        reply, actions = _run(agent.run("Add tasks A and B"))

        assert len(actions) == 2
        assert actions[0].tool == "create_task"
        assert actions[1].tool == "create_task"
        assert actions[0].result["title"] == "Task A"
        assert actions[1].result["title"] == "Task B"

    def test_tool_error_surfaced_in_actions_result(
        self, session: Session, monkeypatch: pytest.MonkeyPatch
    ):
        """Tool returning {"error": ...} is recorded in actions, not raised."""
        agent = TaskAgent(session, TEST_USER)
        call_count = 0

        async def fake_llm(messages):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return LLMMessage(
                    content=None,
                    stop_reason="tool_calls",
                    tool_calls=[
                        LLMToolCall(id="tc1", name="toggle_complete", args={"id": 9999})
                    ],
                )
            return LLMMessage(content="Task #9999 was not found.", stop_reason="stop")

        monkeypatch.setattr(agent, "_call_llm", fake_llm)

        reply, actions = _run(agent.run("Mark task 9999 done"))

        assert "error" in actions[0].result
        assert "not found" in actions[0].result["error"].lower()

    def test_safety_fallback_after_max_iterations(
        self, session: Session, monkeypatch: pytest.MonkeyPatch
    ):
        """If the agent never reaches stop, it returns the fallback reply."""
        agent = TaskAgent(session, TEST_USER)

        async def fake_llm(messages):
            # Always return a tool call — never stop
            return LLMMessage(
                content=None,
                stop_reason="tool_calls",
                tool_calls=[
                    LLMToolCall(id="tc", name="list_tasks", args={"filter": "all"})
                ],
            )

        monkeypatch.setattr(agent, "_call_llm", fake_llm)

        reply, actions = _run(agent.run("Loop forever"))

        # Loop capped at _MAX_ITERATIONS=5 → 5 tool calls
        assert len(actions) == 5
        assert "having trouble" in reply.lower()

    def test_off_topic_returns_reply_with_empty_actions(
        self, session: Session, monkeypatch: pytest.MonkeyPatch
    ):
        # References: specs/features/chatbot.md §US-CHAT-05
        agent = TaskAgent(session, TEST_USER)

        async def fake_llm(messages):
            return LLMMessage(
                content=(
                    "I can only help with task management. "
                    "Try asking me to list or create tasks!"
                ),
                stop_reason="stop",
            )

        monkeypatch.setattr(agent, "_call_llm", fake_llm)

        reply, actions = _run(agent.run("What's the weather today?"))

        assert actions == []
        assert "task" in reply.lower()

    def test_user_isolation_enforced_in_tools(
        self, session: Session, monkeypatch: pytest.MonkeyPatch
    ):
        # References: specs/features/chatbot.md §US-CHAT-06
        other_task = _seed_task(session, "Private", user_id=OTHER_USER)
        agent = TaskAgent(session, TEST_USER)  # different user
        call_count = 0

        async def fake_llm(messages):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return LLMMessage(
                    content=None,
                    stop_reason="tool_calls",
                    tool_calls=[
                        LLMToolCall(
                            id="tc1",
                            name="toggle_complete",
                            args={"id": other_task.id},
                        )
                    ],
                )
            return LLMMessage(content="Done.", stop_reason="stop")

        monkeypatch.setattr(agent, "_call_llm", fake_llm)

        _, actions = _run(agent.run("Toggle the other user's task"))

        # Tool should have returned an error — task not accessible
        assert "error" in actions[0].result


# ---------------------------------------------------------------------------
# _local_simulate — keyword-based simulation (no OPENAI_API_KEY)
# References: specs/agents/agent-behavior.md §LLM Interface (_call_llm)
# ---------------------------------------------------------------------------


class TestLocalSimulation:
    """Tests for TaskAgent._local_simulate and its integration with _call_llm."""

    def _msgs(self, user_text: str) -> list[dict]:
        return [
            {"role": "system", "content": "system prompt"},
            {"role": "user", "content": user_text},
        ]

    def test_add_keyword_returns_task_creation_reply(self, session: Session):
        # References: specs/agents/agent-behavior.md §LLM Interface (_call_llm)
        # _local_simulate now returns tool_calls so the agentic loop executes
        # the real create_task tool and persists to the database.
        agent = TaskAgent(session, TEST_USER)
        result = agent._local_simulate(self._msgs("I want to add a task"))
        assert result.stop_reason == "tool_calls"
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "create_task"

    def test_delete_keyword_without_id_asks_for_clarification(self, session: Session):
        # No task number in message → clarification prompt (stop, no tool call).
        agent = TaskAgent(session, TEST_USER)
        result = agent._local_simulate(self._msgs("please delete that task"))
        assert result.stop_reason == "stop"
        assert result.content is not None
        assert "task number" in result.content.lower() or "which" in result.content.lower()

    def test_delete_keyword_with_id_returns_tool_call(self, session: Session):
        # Task number present → delete_task tool call.
        agent = TaskAgent(session, TEST_USER)
        result = agent._local_simulate(self._msgs("delete task 3"))
        assert result.stop_reason == "tool_calls"
        assert result.tool_calls[0].name == "delete_task"
        assert result.tool_calls[0].args["id"] == 3

    def test_list_keyword_returns_list_tasks_tool_call(self, session: Session):
        # _local_simulate now returns tool_calls so list_tasks executes against DB.
        agent = TaskAgent(session, TEST_USER)
        result = agent._local_simulate(self._msgs("list my tasks"))
        assert result.stop_reason == "tool_calls"
        assert result.tool_calls[0].name == "list_tasks"

    def test_hello_keyword_returns_greeting(self, session: Session):
        agent = TaskAgent(session, TEST_USER)
        result = agent._local_simulate(self._msgs("hello there"))
        assert result.stop_reason == "stop"
        assert result.content is not None
        assert "hello" in result.content.lower()

    def test_hi_keyword_returns_greeting(self, session: Session):
        agent = TaskAgent(session, TEST_USER)
        result = agent._local_simulate(self._msgs("hi!"))
        assert result.stop_reason == "stop"
        assert result.content  # non-empty reply

    def test_unknown_message_returns_fallback_help(self, session: Session):
        agent = TaskAgent(session, TEST_USER)
        result = agent._local_simulate(self._msgs("what is the weather outside?"))
        assert result.stop_reason == "stop"
        assert result.content  # fallback help text is non-empty

    def test_matching_is_case_insensitive(self, session: Session):
        agent = TaskAgent(session, TEST_USER)
        result = agent._local_simulate(self._msgs("ADD a new item"))
        assert result.stop_reason == "tool_calls"
        assert result.tool_calls[0].name == "create_task"

    def test_call_llm_uses_simulation_when_no_api_key(
        self, session: Session, monkeypatch: pytest.MonkeyPatch
    ):
        """_call_llm delegates to _local_simulate when OPENAI_API_KEY is absent."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        agent = TaskAgent(session, TEST_USER)
        messages = [
            {"role": "system", "content": "system prompt"},
            {"role": "user", "content": "list tasks"},
        ]
        result = _run(agent._call_llm(messages))
        # list intent → tool_calls (real list_tasks executes against DB)
        assert result.stop_reason == "tool_calls"
        assert result.tool_calls[0].name == "list_tasks"

    def test_call_llm_simulation_does_not_raise_503(
        self, session: Session, monkeypatch: pytest.MonkeyPatch
    ):
        """Missing API key must not raise HTTPException(503) anymore."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        agent = TaskAgent(session, TEST_USER)
        # Should complete without any exception
        result = _run(agent._call_llm([{"role": "user", "content": "hello"}]))
        assert result.stop_reason == "stop"
        assert result.content  # non-empty reply


# ---------------------------------------------------------------------------
# Extended Pass-1 (intent detection) tests
# References: specs/agents/agent-behavior.md §LLM Interface (_call_llm)
# ---------------------------------------------------------------------------


class TestLocalSimulationPass1Extended:
    """Additional intent-detection tests for _local_simulate Pass 1."""

    def _msgs(self, user_text: str) -> list[dict]:
        return [
            {"role": "system", "content": "system prompt"},
            {"role": "user", "content": user_text},
        ]

    def _msgs_with_today(self, user_text: str, today: str) -> list[dict]:
        return [
            {"role": "system", "content": "system prompt"},
            {"role": "user", "content": f"[Today is {today}] {user_text}"},
        ]

    # ── filter variants ────────────────────────────────────────────────────

    def test_show_pending_returns_pending_filter(self, session: Session):
        agent = TaskAgent(session, TEST_USER)
        result = agent._local_simulate(self._msgs("show pending tasks"))
        assert result.stop_reason == "tool_calls"
        assert result.tool_calls[0].name == "list_tasks"
        assert result.tool_calls[0].args.get("filter") == "pending"

    def test_show_completed_returns_completed_filter(self, session: Session):
        agent = TaskAgent(session, TEST_USER)
        result = agent._local_simulate(self._msgs("show completed tasks"))
        assert result.stop_reason == "tool_calls"
        assert result.tool_calls[0].name == "list_tasks"
        assert result.tool_calls[0].args.get("filter") == "completed"

    def test_show_done_tasks_returns_completed_filter(self, session: Session):
        agent = TaskAgent(session, TEST_USER)
        result = agent._local_simulate(self._msgs("show done tasks"))
        assert result.stop_reason == "tool_calls"
        assert result.tool_calls[0].args.get("filter") == "completed"

    # ── toggle / complete ──────────────────────────────────────────────────

    def test_toggle_without_id_asks_clarification(self, session: Session):
        agent = TaskAgent(session, TEST_USER)
        result = agent._local_simulate(self._msgs("mark task as done"))
        assert result.stop_reason == "stop"
        assert result.content is not None

    def test_complete_with_id_returns_toggle_tool_call(self, session: Session):
        agent = TaskAgent(session, TEST_USER)
        result = agent._local_simulate(self._msgs("complete task 7"))
        assert result.stop_reason == "tool_calls"
        assert result.tool_calls[0].name == "toggle_complete"
        assert result.tool_calls[0].args["id"] == 7

    def test_mark_task_done_with_id_returns_toggle_tool_call(self, session: Session):
        agent = TaskAgent(session, TEST_USER)
        result = agent._local_simulate(self._msgs("mark task 2 done"))
        assert result.stop_reason == "tool_calls"
        assert result.tool_calls[0].name == "toggle_complete"
        assert result.tool_calls[0].args["id"] == 2

    # ── create keyword variants ────────────────────────────────────────────

    def test_create_keyword_triggers_create_task(self, session: Session):
        agent = TaskAgent(session, TEST_USER)
        result = agent._local_simulate(self._msgs("create buy groceries"))
        assert result.stop_reason == "tool_calls"
        assert result.tool_calls[0].name == "create_task"

    def test_title_capitalized_in_create_task(self, session: Session):
        agent = TaskAgent(session, TEST_USER)
        result = agent._local_simulate(self._msgs("add buy milk"))
        title = result.tool_calls[0].args.get("title", "")
        assert title[0].isupper(), f"Expected capitalized title, got {title!r}"

    # ── due_date natural language ──────────────────────────────────────────

    def test_add_tomorrow_injects_next_day_due_date(self, session: Session):
        agent = TaskAgent(session, TEST_USER)
        result = agent._local_simulate(self._msgs_with_today("add meeting tomorrow", "2026-03-10"))
        assert result.stop_reason == "tool_calls"
        assert result.tool_calls[0].name == "create_task"
        due = result.tool_calls[0].args.get("due_date", "")
        assert due.startswith("2026-03-11"), f"Expected 2026-03-11 date, got {due!r}"

    def test_add_today_injects_same_day_due_date(self, session: Session):
        agent = TaskAgent(session, TEST_USER)
        result = agent._local_simulate(self._msgs_with_today("add standup today", "2026-03-10"))
        assert result.stop_reason == "tool_calls"
        due = result.tool_calls[0].args.get("due_date", "")
        assert due.startswith("2026-03-10"), f"Expected 2026-03-10 date, got {due!r}"

    def test_add_tomorrow_at_2pm_sets_14_hour(self, session: Session):
        agent = TaskAgent(session, TEST_USER)
        result = agent._local_simulate(
            self._msgs_with_today("add meeting tomorrow at 2 PM", "2026-03-10")
        )
        due = result.tool_calls[0].args.get("due_date", "")
        assert "T14:00:00" in due, f"Expected T14:00:00 in due_date, got {due!r}"

    def test_add_tomorrow_at_9am_sets_9_hour(self, session: Session):
        agent = TaskAgent(session, TEST_USER)
        result = agent._local_simulate(
            self._msgs_with_today("add standup tomorrow at 9 AM", "2026-03-10")
        )
        due = result.tool_calls[0].args.get("due_date", "")
        assert "T09:00:00" in due, f"Expected T09:00:00 in due_date, got {due!r}"

    def test_no_today_prefix_means_no_due_date(self, session: Session):
        # Without [Today is ...] the agent cannot know the date → no due_date
        agent = TaskAgent(session, TEST_USER)
        result = agent._local_simulate(self._msgs("add meeting tomorrow"))
        assert result.stop_reason == "tool_calls"
        assert result.tool_calls[0].args.get("due_date") is None


# ---------------------------------------------------------------------------
# Pass-2 (reply generation) tests
# References: specs/agents/agent-behavior.md §LLM Interface (_call_llm)
# ---------------------------------------------------------------------------


class TestLocalSimulationPass2:
    """Tests for _local_simulate Pass 2: friendly reply after tool results."""

    def _msgs_with_result(
        self, user_text: str, tool_name: str, result: dict
    ) -> list[dict]:
        """Build messages that include an assistant tool_call + tool result."""
        import json as _j

        return [
            {"role": "system", "content": "system"},
            {"role": "user", "content": user_text},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "tc1",
                        "type": "function",
                        "function": {"name": tool_name, "arguments": "{}"},
                    }
                ],
            },
            {
                "role": "tool",
                "tool_call_id": "tc1",
                "content": _j.dumps(result),
            },
        ]

    # ── create_task replies ────────────────────────────────────────────────

    def test_create_task_reply_contains_title(self, session: Session):
        agent = TaskAgent(session, TEST_USER)
        msgs = self._msgs_with_result(
            "add buy milk",
            "create_task",
            {"id": 1, "title": "Buy milk", "description": "", "completed": False, "due_date": None},
        )
        result = agent._local_simulate(msgs)
        assert result.stop_reason == "stop"
        assert "Buy milk" in (result.content or "")

    def test_create_task_with_due_date_shows_date_in_reply(self, session: Session):
        agent = TaskAgent(session, TEST_USER)
        msgs = self._msgs_with_result(
            "add meeting tomorrow",
            "create_task",
            {"id": 2, "title": "Meeting", "description": "", "completed": False,
             "due_date": "2026-03-11T09:00:00"},
        )
        result = agent._local_simulate(msgs)
        assert result.stop_reason == "stop"
        assert "2026-03-11" in (result.content or "")

    def test_create_task_without_due_date_no_date_in_reply(self, session: Session):
        agent = TaskAgent(session, TEST_USER)
        msgs = self._msgs_with_result(
            "add buy milk",
            "create_task",
            {"id": 1, "title": "Buy milk", "description": "", "completed": False, "due_date": None},
        )
        result = agent._local_simulate(msgs)
        # Should NOT mention a date when none was set
        assert "due" not in (result.content or "").lower()

    # ── list_tasks replies ─────────────────────────────────────────────────

    def test_list_tasks_empty_says_no_tasks(self, session: Session):
        agent = TaskAgent(session, TEST_USER)
        msgs = self._msgs_with_result(
            "list tasks", "list_tasks", {"tasks": [], "count": 0}
        )
        result = agent._local_simulate(msgs)
        assert result.stop_reason == "stop"
        assert "no tasks" in (result.content or "").lower()

    def test_list_tasks_shows_all_titles(self, session: Session):
        agent = TaskAgent(session, TEST_USER)
        msgs = self._msgs_with_result(
            "list tasks",
            "list_tasks",
            {
                "tasks": [
                    {"id": 1, "title": "Buy milk", "completed": False, "due_date": None},
                    {"id": 2, "title": "Go to gym", "completed": True, "due_date": None},
                ],
                "count": 2,
            },
        )
        result = agent._local_simulate(msgs)
        assert result.stop_reason == "stop"
        assert "Buy milk" in (result.content or "")
        assert "Go to gym" in (result.content or "")

    def test_list_tasks_completed_shows_checkmark(self, session: Session):
        agent = TaskAgent(session, TEST_USER)
        msgs = self._msgs_with_result(
            "list tasks",
            "list_tasks",
            {"tasks": [{"id": 1, "title": "Done", "completed": True, "due_date": None}], "count": 1},
        )
        result = agent._local_simulate(msgs)
        assert "✓" in (result.content or "")

    def test_list_tasks_shows_due_date_when_present(self, session: Session):
        agent = TaskAgent(session, TEST_USER)
        msgs = self._msgs_with_result(
            "list tasks",
            "list_tasks",
            {
                "tasks": [
                    {"id": 1, "title": "Meeting", "completed": False,
                     "due_date": "2026-03-11T14:00:00"},
                ],
                "count": 1,
            },
        )
        result = agent._local_simulate(msgs)
        assert "2026-03-11" in (result.content or "")

    # ── delete_task replies ────────────────────────────────────────────────

    def test_delete_task_reply_confirms_deletion(self, session: Session):
        agent = TaskAgent(session, TEST_USER)
        msgs = self._msgs_with_result(
            "delete task 3",
            "delete_task",
            {"deleted": True, "id": 3, "title": "Old task"},
        )
        result = agent._local_simulate(msgs)
        assert result.stop_reason == "stop"
        assert "deleted" in (result.content or "").lower() or "Old task" in (result.content or "")

    # ── toggle_complete replies ────────────────────────────────────────────

    def test_toggle_complete_reply_says_completed(self, session: Session):
        agent = TaskAgent(session, TEST_USER)
        msgs = self._msgs_with_result(
            "complete task 1",
            "toggle_complete",
            {"id": 1, "title": "Buy milk", "completed": True},
        )
        result = agent._local_simulate(msgs)
        assert result.stop_reason == "stop"
        assert "completed" in (result.content or "").lower() or "✓" in (result.content or "")

    def test_toggle_uncomplete_reply_says_pending(self, session: Session):
        agent = TaskAgent(session, TEST_USER)
        msgs = self._msgs_with_result(
            "toggle task 2",
            "toggle_complete",
            {"id": 2, "title": "Go to gym", "completed": False},
        )
        result = agent._local_simulate(msgs)
        assert result.stop_reason == "stop"
        assert "pending" in (result.content or "").lower()

    # ── error replies ──────────────────────────────────────────────────────

    def test_tool_error_returns_sorry_message(self, session: Session):
        agent = TaskAgent(session, TEST_USER)
        msgs = self._msgs_with_result(
            "delete task 99",
            "delete_task",
            {"error": "Task #99 not found."},
        )
        result = agent._local_simulate(msgs)
        assert result.stop_reason == "stop"
        assert (
            "sorry" in (result.content or "").lower()
            or "couldn't" in (result.content or "").lower()
        )


# ---------------------------------------------------------------------------
# End-to-end agent.run() with _local_simulate (no OPENAI_API_KEY)
# References: specs/agents/agent-behavior.md §Agentic Loop
# ---------------------------------------------------------------------------


class TestAgentRunLocalSimulation:
    """agent.run() end-to-end tests; _local_simulate drives all tool calls."""

    def test_add_task_creates_in_db(
        self, session: Session, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        agent = TaskAgent(session, TEST_USER)
        reply, actions = _run(agent.run("add buy milk"))
        assert any(a.tool == "create_task" for a in actions)
        assert reply  # non-empty reply

    def test_add_task_reply_contains_title(
        self, session: Session, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        agent = TaskAgent(session, TEST_USER)
        reply, _ = _run(agent.run("add morning jog"))
        # title extraction strips filler words; check key word is present
        assert "morning" in reply.lower() or "jog" in reply.lower()

    def test_list_tasks_empty_returns_no_tasks_reply(
        self, session: Session, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        agent = TaskAgent(session, TEST_USER)
        reply, actions = _run(agent.run("list my tasks"))
        assert any(a.tool == "list_tasks" for a in actions)
        assert "no tasks" in reply.lower()

    def test_list_tasks_after_add_shows_task_title(
        self, session: Session, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        agent = TaskAgent(session, TEST_USER)
        _run(agent.run("add buy groceries"))
        reply, actions = _run(agent.run("list my tasks"))
        assert any(a.tool == "list_tasks" for a in actions)
        assert "groceries" in reply.lower() or "Buy groceries" in reply

    def test_complete_task_toggles_to_done(
        self, session: Session, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        agent = TaskAgent(session, TEST_USER)
        # "write report" avoids "finish"/"done" keywords that would trigger toggle
        _, add_actions = _run(agent.run("add write report"))
        task_id = add_actions[0].result["id"]
        _, toggle_actions = _run(agent.run(f"complete task {task_id}"))
        assert any(a.tool == "toggle_complete" for a in toggle_actions)
        assert toggle_actions[0].result["completed"] is True

    def test_delete_task_removes_from_db_and_confirms(
        self, session: Session, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        agent = TaskAgent(session, TEST_USER)
        _, add_actions = _run(agent.run("add temp task"))
        task_id = add_actions[0].result["id"]
        reply, del_actions = _run(agent.run(f"delete task {task_id}"))
        assert any(a.tool == "delete_task" for a in del_actions)
        assert del_actions[0].result.get("deleted") is True

    def test_today_param_sets_due_date_for_tomorrow(
        self, session: Session, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        agent = TaskAgent(session, TEST_USER)
        _, actions = _run(agent.run("add meeting tomorrow", today="2026-03-10"))
        assert actions[0].tool == "create_task"
        due = actions[0].result.get("due_date") or ""
        assert "2026-03-11" in due

    def test_today_param_with_time_sets_correct_hour(
        self, session: Session, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        agent = TaskAgent(session, TEST_USER)
        _, actions = _run(agent.run("add meeting tomorrow at 3 PM", today="2026-03-10"))
        assert actions[0].tool == "create_task"
        due = actions[0].result.get("due_date") or ""
        assert "2026-03-11" in due
        assert "15:00" in due

    def test_user_isolation_in_local_simulate(
        self, session: Session, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        # User A adds a task
        agent_a = TaskAgent(session, "user-a")
        _run(agent_a.run("add user a task"))
        # User B lists tasks — must see 0 tasks
        agent_b = TaskAgent(session, "user-b")
        _, actions = _run(agent_b.run("list my tasks"))
        task_list = actions[0].result.get("tasks", [])
        assert task_list == [], f"User B should see no tasks, got {task_list}"
