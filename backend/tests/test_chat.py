# tests/test_chat.py — Integration tests for POST /api/chat (Phase III agent)
# References: specs/api/chat-endpoint.md §Acceptance Criteria
#             specs/agents/agent-behavior.md §Request Lifecycle
#             specs/api/rest-endpoints.md §Error Taxonomy
#
# The LLM is monkeypatched at the class level so no OPENAI_API_KEY is needed.
# The DB session is overridden with an in-memory SQLite instance so tool calls
# that touch the DB work correctly.

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from agents.agent import LLMMessage, TaskAgent
from src.app import app
from src.auth.dependencies import get_current_user
from src.database import get_session

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TEST_USER = "user-test-001"

# A fixed fake LLM response used for most tests — no tool calls, just a reply.
_SIMPLE_REPLY = "I can help you manage your tasks!"


async def _fake_llm_simple(self: TaskAgent, messages: list[dict]) -> LLMMessage:
    """Monkeypatch target: returns a plain stop reply with no tool calls."""
    return LLMMessage(content=_SIMPLE_REPLY, stop_reason="stop")


@pytest.fixture(name="session")
def session_fixture():
    """Fresh in-memory SQLite per test (tools may read/write the DB)."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="client")
def client_fixture(session: Session, monkeypatch: pytest.MonkeyPatch):
    """TestClient with session + auth overridden, LLM monkeypatched."""
    monkeypatch.setattr(TaskAgent, "_call_llm", _fake_llm_simple)

    def _override_session():
        yield session

    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[get_current_user] = lambda: TEST_USER
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /api/chat — response structure
# ---------------------------------------------------------------------------


class TestChatResponseStructure:
    def test_valid_message_returns_200(self, client: TestClient):
        # References: specs/api/chat-endpoint.md §AC-1
        r = client.post("/api/chat", json={"message": "Hello"})
        assert r.status_code == 200

    def test_response_has_reply_trace_id_and_actions(self, client: TestClient):
        # References: specs/api/chat-endpoint.md §ChatResponse
        r = client.post("/api/chat", json={"message": "Hi"})
        assert {"reply", "trace_id", "actions"} <= r.json().keys()

    def test_reply_is_non_empty_string(self, client: TestClient):
        r = client.post("/api/chat", json={"message": "Help"})
        assert isinstance(r.json()["reply"], str)
        assert r.json()["reply"]

    def test_actions_is_a_list(self, client: TestClient):
        # Agent with no tool calls → empty list
        r = client.post("/api/chat", json={"message": "Hi"})
        assert isinstance(r.json()["actions"], list)

    def test_trace_id_is_present_and_non_empty(self, client: TestClient):
        # References: specs/api/chat-endpoint.md §AC-3
        r = client.post("/api/chat", json={"message": "Hello"})
        assert r.json()["trace_id"]

    def test_trace_id_is_unique_per_request(self, client: TestClient):
        # References: specs/api/chat-endpoint.md §AC-3
        r1 = client.post("/api/chat", json={"message": "Hello"})
        r2 = client.post("/api/chat", json={"message": "Hello"})
        assert r1.json()["trace_id"] != r2.json()["trace_id"]


# ---------------------------------------------------------------------------
# POST /api/chat — input validation
# ---------------------------------------------------------------------------


class TestChatValidation:
    def test_empty_message_returns_400(self, client: TestClient):
        # References: specs/api/chat-endpoint.md §AC-4
        r = client.post("/api/chat", json={"message": ""})
        assert r.status_code == 400
        assert "empty" in r.json()["detail"].lower()

    def test_whitespace_only_message_returns_400(self, client: TestClient):
        # References: specs/api/chat-endpoint.md §AC-4
        r = client.post("/api/chat", json={"message": "   "})
        assert r.status_code == 400


# ---------------------------------------------------------------------------
# POST /api/chat — tool call reflected in actions
# ---------------------------------------------------------------------------


class TestChatActions:
    def test_action_trace_fields_present(
        self, session: Session, monkeypatch: pytest.MonkeyPatch
    ):
        """When the agent calls a tool, its trace appears in actions."""
        from agents.agent import LLMToolCall

        call_count = 0

        async def fake_llm_with_tool(self: TaskAgent, messages: list) -> LLMMessage:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return LLMMessage(
                    content=None,
                    stop_reason="tool_calls",
                    tool_calls=[
                        LLMToolCall(
                            id="tc1",
                            name="create_task",
                            args={"title": "Buy milk"},
                        )
                    ],
                )
            return LLMMessage(
                content="Done! I created task 'Buy milk'.",
                stop_reason="stop",
            )

        monkeypatch.setattr(TaskAgent, "_call_llm", fake_llm_with_tool)

        def _override_session():
            yield session

        app.dependency_overrides[get_session] = _override_session
        app.dependency_overrides[get_current_user] = lambda: TEST_USER

        with TestClient(app) as client:
            r = client.post("/api/chat", json={"message": "Add a task to buy milk"})
        app.dependency_overrides.clear()

        assert r.status_code == 200
        actions = r.json()["actions"]
        assert len(actions) == 1
        assert actions[0]["tool"] == "create_task"
        assert actions[0]["args"]["title"] == "Buy milk"
        assert "id" in actions[0]["result"]  # task was actually created


# ---------------------------------------------------------------------------
# POST /api/chat — safe mode fallback
# ---------------------------------------------------------------------------


class TestChatSafeMode:
    def test_agent_exception_returns_200_with_echo(
        self, session: Session, monkeypatch: pytest.MonkeyPatch
    ):
        """Any exception from the agent must fall back to echo, not crash."""

        async def exploding_llm(self: TaskAgent, messages: list) -> LLMMessage:
            raise RuntimeError("Simulated agent failure")

        monkeypatch.setattr(TaskAgent, "_call_llm", exploding_llm)

        def _override_session():
            yield session

        app.dependency_overrides[get_session] = _override_session
        app.dependency_overrides[get_current_user] = lambda: TEST_USER

        with TestClient(app) as client:
            r = client.post("/api/chat", json={"message": "Hello"})
        app.dependency_overrides.clear()

        assert r.status_code == 200
        assert r.json()["reply"] == "You said: Hello"
        assert r.json()["actions"] == []

    def test_missing_api_key_returns_200_with_echo(
        self, session: Session, monkeypatch: pytest.MonkeyPatch
    ):
        """HTTP 503 from the agent (no key) is caught and returns echo reply."""
        from fastapi import HTTPException as FastAPIHTTPException

        async def no_key_llm(self: TaskAgent, messages: list) -> LLMMessage:
            raise FastAPIHTTPException(
                status_code=503,
                detail="AI service not configured. Set OPENAI_API_KEY.",
            )

        monkeypatch.setattr(TaskAgent, "_call_llm", no_key_llm)

        def _override_session():
            yield session

        app.dependency_overrides[get_session] = _override_session
        app.dependency_overrides[get_current_user] = lambda: TEST_USER

        with TestClient(app) as client:
            r = client.post("/api/chat", json={"message": "List my tasks"})
        app.dependency_overrides.clear()

        assert r.status_code == 200
        assert r.json()["reply"] == "You said: List my tasks"

    def test_echo_uses_stripped_message(
        self, session: Session, monkeypatch: pytest.MonkeyPatch
    ):
        """Fallback echo strips whitespace, matching the input validation path."""

        async def exploding_llm(self: TaskAgent, messages: list) -> LLMMessage:
            raise RuntimeError("fail")

        monkeypatch.setattr(TaskAgent, "_call_llm", exploding_llm)

        def _override_session():
            yield session

        app.dependency_overrides[get_session] = _override_session
        app.dependency_overrides[get_current_user] = lambda: TEST_USER

        with TestClient(app) as client:
            r = client.post("/api/chat", json={"message": "  trim me  "})
        app.dependency_overrides.clear()

        assert r.status_code == 200
        assert r.json()["reply"] == "You said: trim me"


# ---------------------------------------------------------------------------
# POST /api/chat — auth behaviour (no override)
# ---------------------------------------------------------------------------


class TestChatAuth:
    def test_missing_token_returns_401(self):
        # References: specs/api/chat-endpoint.md §AC-5
        app.dependency_overrides.clear()
        with TestClient(app) as bare_client:
            r = bare_client.post("/api/chat", json={"message": "Hello"})
        assert r.status_code == 401
        assert r.json()["detail"] == "Not authenticated."

    def test_invalid_token_returns_401(self):
        # References: specs/api/chat-endpoint.md §AC-6
        app.dependency_overrides.clear()
        with TestClient(app) as bare_client:
            r = bare_client.post(
                "/api/chat",
                json={"message": "Hello"},
                headers={"Authorization": "Bearer not-a-real-jwt"},
            )
        assert r.status_code == 401
        assert r.json()["detail"] == "Invalid token."


# ---------------------------------------------------------------------------
# POST /api/chat — today field forwarding
# References: specs/features/chatbot.md §FR-CHAT-011
# ---------------------------------------------------------------------------


class TestChatTodayField:
    """Tests for the optional `today` field in ChatRequest."""

    def test_today_field_is_optional(self, client: TestClient):
        # Request without today must still return 200
        r = client.post("/api/chat", json={"message": "Hello"})
        assert r.status_code == 200

    def test_today_field_accepted_in_request(self, client: TestClient):
        r = client.post("/api/chat", json={"message": "Hello", "today": "2026-03-10"})
        assert r.status_code == 200

    def test_today_field_null_is_accepted(self, client: TestClient):
        r = client.post("/api/chat", json={"message": "Hello", "today": None})
        assert r.status_code == 200

    def test_today_forwarded_to_agent_run(
        self, session: Session, monkeypatch: pytest.MonkeyPatch
    ):
        """today value must reach agent.run() so due_date injection works."""
        received_today: list = []

        original_run = TaskAgent.run

        async def capturing_run(self_agent, user_message, today=None, dry_run=False):
            received_today.append(today)
            return await original_run(self_agent, user_message, today=today, dry_run=dry_run)

        monkeypatch.setattr(TaskAgent, "run", capturing_run)
        monkeypatch.setattr(TaskAgent, "_call_llm", _fake_llm_simple)

        def _override_session():
            yield session

        app.dependency_overrides[get_session] = _override_session
        app.dependency_overrides[get_current_user] = lambda: TEST_USER

        with TestClient(app) as client:
            client.post("/api/chat", json={"message": "add task", "today": "2026-03-10"})
        app.dependency_overrides.clear()

        assert received_today == ["2026-03-10"]


# ---------------------------------------------------------------------------
# POST /api/chat — extended tool action tests
# References: specs/api/chat-endpoint.md §ActionTraceOut
# ---------------------------------------------------------------------------


class TestChatToolActionsExtended:
    """Action trace tests for list_tasks, toggle_complete, delete_task."""

    def _setup(self, monkeypatch, session, tool_name, tool_args):
        """Wire a fake LLM that calls one tool then stops."""
        from agents.agent import LLMToolCall

        call_count = 0

        async def fake_llm(self_agent: TaskAgent, messages: list) -> LLMMessage:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return LLMMessage(
                    content=None,
                    stop_reason="tool_calls",
                    tool_calls=[LLMToolCall(id="tc1", name=tool_name, args=tool_args)],
                )
            return LLMMessage(content="Done!", stop_reason="stop")

        monkeypatch.setattr(TaskAgent, "_call_llm", fake_llm)

        def _override_session():
            yield session

        app.dependency_overrides[get_session] = _override_session
        app.dependency_overrides[get_current_user] = lambda: TEST_USER

    def test_list_tasks_action_recorded(
        self, session: Session, monkeypatch: pytest.MonkeyPatch
    ):
        self._setup(monkeypatch, session, "list_tasks", {})
        with TestClient(app) as client:
            r = client.post("/api/chat", json={"message": "list my tasks"})
        app.dependency_overrides.clear()

        assert r.status_code == 200
        actions = r.json()["actions"]
        assert len(actions) == 1
        assert actions[0]["tool"] == "list_tasks"
        assert "tasks" in actions[0]["result"]

    def test_list_pending_filter_passed_to_tool(
        self, session: Session, monkeypatch: pytest.MonkeyPatch
    ):
        self._setup(monkeypatch, session, "list_tasks", {"filter": "pending"})
        with TestClient(app) as client:
            r = client.post("/api/chat", json={"message": "show pending tasks"})
        app.dependency_overrides.clear()

        actions = r.json()["actions"]
        assert actions[0]["args"].get("filter") == "pending"

    def test_toggle_complete_action_recorded(
        self, session: Session, monkeypatch: pytest.MonkeyPatch
    ):
        from agents.tools import create_task

        task = create_task(session, TEST_USER, "test task")
        task_id = task["id"]
        self._setup(monkeypatch, session, "toggle_complete", {"id": task_id})

        with TestClient(app) as client:
            r = client.post("/api/chat", json={"message": f"complete task {task_id}"})
        app.dependency_overrides.clear()

        assert r.status_code == 200
        actions = r.json()["actions"]
        assert actions[0]["tool"] == "toggle_complete"
        assert actions[0]["result"]["completed"] is True

    def test_delete_task_action_recorded(
        self, session: Session, monkeypatch: pytest.MonkeyPatch
    ):
        from agents.tools import create_task

        task = create_task(session, TEST_USER, "to be deleted")
        task_id = task["id"]
        self._setup(monkeypatch, session, "delete_task", {"id": task_id})

        with TestClient(app) as client:
            r = client.post("/api/chat", json={"message": f"delete task {task_id}"})
        app.dependency_overrides.clear()

        assert r.status_code == 200
        actions = r.json()["actions"]
        assert actions[0]["tool"] == "delete_task"
        assert actions[0]["result"]["deleted"] is True

    def test_multiple_actions_all_recorded(
        self, session: Session, monkeypatch: pytest.MonkeyPatch
    ):
        """If LLM calls two tools in sequence, both appear in actions list."""
        from agents.agent import LLMToolCall
        from agents.tools import create_task

        task = create_task(session, TEST_USER, "multi-step task")
        task_id = task["id"]

        call_count = 0

        async def fake_llm_two_tools(self_agent: TaskAgent, messages: list) -> LLMMessage:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return LLMMessage(
                    content=None,
                    stop_reason="tool_calls",
                    tool_calls=[LLMToolCall(id="tc1", name="list_tasks", args={})],
                )
            if call_count == 2:
                return LLMMessage(
                    content=None,
                    stop_reason="tool_calls",
                    tool_calls=[
                        LLMToolCall(id="tc2", name="toggle_complete", args={"id": task_id})
                    ],
                )
            return LLMMessage(content="All done!", stop_reason="stop")

        monkeypatch.setattr(TaskAgent, "_call_llm", fake_llm_two_tools)

        def _override_session():
            yield session

        app.dependency_overrides[get_session] = _override_session
        app.dependency_overrides[get_current_user] = lambda: TEST_USER

        with TestClient(app) as client:
            r = client.post("/api/chat", json={"message": "list then complete"})
        app.dependency_overrides.clear()

        assert r.status_code == 200
        tools_called = [a["tool"] for a in r.json()["actions"]]
        assert "list_tasks" in tools_called
        assert "toggle_complete" in tools_called
