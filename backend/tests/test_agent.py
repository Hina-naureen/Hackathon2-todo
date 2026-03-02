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
