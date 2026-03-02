# tests/test_events.py — Unit + integration tests for Phase V event publisher
# References: specs/phase5-dapr-kafka.md §Acceptance Criteria
#             specs/phase5-dapr-kafka.md §Dapr Integration Architecture
#
# Strategy:
#   - Monkeypatch httpx.AsyncClient to avoid real network calls.
#   - Monkeypatch os.environ to test DAPR_HTTP_PORT presence / absence.
#   - Integration tests use the FastAPI TestClient with dependency overrides
#     to verify that route handlers call publish_task_event after DB commits.

from __future__ import annotations

import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

import src.events as events_module
from src.app import app
from src.auth.dependencies import get_current_user
from src.database import get_session

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

TEST_USER = "user-test-events-001"


@pytest.fixture(name="db_session")
def db_session_fixture():
    """Fresh in-memory SQLite per test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="api_client")
def api_client_fixture(db_session: Session):
    """TestClient with auth + session overridden."""

    def _override_session():
        yield db_session

    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[get_current_user] = lambda: TEST_USER

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Unit tests: publish_task_event()
# References: specs/phase5-dapr-kafka.md §AC-P5-001, AC-P5-002, AC-P5-003
# ---------------------------------------------------------------------------


class TestPublishTaskEvent:
    """Tests for src.events.publish_task_event — isolated from real Dapr."""

    @pytest.mark.asyncio
    async def test_publish_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """AC-P5-001: succeeds when Dapr sidecar returns 2xx."""
        monkeypatch.setattr(events_module, "_DAPR_HTTP_PORT", "3500")

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("src.events.httpx.AsyncClient", return_value=mock_client):
            await events_module.publish_task_event(
                "task.created", 1, "user-abc", extra={"title": "Buy milk"}
            )

        mock_client.post.assert_awaited_once()
        call_args = mock_client.post.call_args
        assert "task-events" in call_args.args[0]
        payload = call_args.kwargs["json"]
        assert payload["event_type"] == "task.created"
        assert payload["task_id"] == 1
        assert payload["user_id"] == "user-abc"
        assert payload["title"] == "Buy milk"
        assert "timestamp" in payload

    @pytest.mark.asyncio
    async def test_publish_sidecar_unreachable_does_not_raise(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """AC-P5-002: logs WARNING and does NOT raise when sidecar is down."""
        monkeypatch.setattr(events_module, "_DAPR_HTTP_PORT", "3500")

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(
            side_effect=ConnectionRefusedError("Connection refused")
        )

        with caplog.at_level(logging.WARNING, logger="src.events"):
            with patch("src.events.httpx.AsyncClient", return_value=mock_client):
                # Must NOT raise
                await events_module.publish_task_event("task.deleted", 5, "user-xyz")

        assert any("Dapr publish failed" in r.message for r in caplog.records)

    @pytest.mark.asyncio
    async def test_publish_skipped_when_dapr_not_configured(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """AC-P5-003: no-op when DAPR_HTTP_PORT is absent (non-Dapr deployment)."""
        monkeypatch.setattr(events_module, "_DAPR_HTTP_PORT", None)

        with patch("src.events.httpx.AsyncClient") as mock_cls:
            await events_module.publish_task_event("task.created", 1, "user-abc")

        mock_cls.assert_not_called()

    @pytest.mark.asyncio
    async def test_publish_http_error_does_not_raise(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Non-2xx response is caught and logged as WARNING — no exception raised."""
        monkeypatch.setattr(events_module, "_DAPR_HTTP_PORT", "3500")

        import httpx as _httpx

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock(
            side_effect=_httpx.HTTPStatusError(
                "500 Internal Server Error",
                request=MagicMock(),
                response=MagicMock(),
            )
        )

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)

        with caplog.at_level(logging.WARNING, logger="src.events"):
            with patch("src.events.httpx.AsyncClient", return_value=mock_client):
                await events_module.publish_task_event("task.toggled", 3, "u")

        assert any("Dapr publish failed" in r.message for r in caplog.records)

    @pytest.mark.asyncio
    async def test_publish_extra_fields_included(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Extra kwargs are merged into the event payload."""
        monkeypatch.setattr(events_module, "_DAPR_HTTP_PORT", "3500")

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("src.events.httpx.AsyncClient", return_value=mock_client):
            await events_module.publish_task_event(
                "task.toggled", 7, "u", extra={"completed": True}
            )

        payload = mock_client.post.call_args.kwargs["json"]
        assert payload["completed"] is True


# ---------------------------------------------------------------------------
# Integration tests: route handlers emit events
# References: specs/phase5-dapr-kafka.md §AC-P5-004, AC-P5-005
# ---------------------------------------------------------------------------


class TestRouteEventEmission:
    """Verify that task route mutations call publish_task_event."""

    def test_create_task_emits_event(
        self, api_client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """AC-P5-004: POST /api/tasks calls publish_task_event('task.created', ...)."""
        published: list[tuple] = []

        async def _fake_publish(
            event_type, task_id, user_id, extra=None
        ):
            published.append((event_type, task_id, user_id))

        monkeypatch.setattr(
            "src.routes.tasks.publish_task_event", _fake_publish
        )

        resp = api_client.post("/api/tasks", json={"title": "Test task"})
        assert resp.status_code == 201

        assert len(published) == 1
        assert published[0][0] == "task.created"
        assert published[0][2] == TEST_USER

    def test_delete_task_emits_event(
        self, api_client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """AC-P5-005: DELETE /api/tasks/{id} calls publish_task_event('task.deleted', ...)."""
        # Create a task first (monkeypatch publish so it doesn't interfere)
        published: list[tuple] = []

        async def _fake_publish(event_type, task_id, user_id, extra=None):
            published.append((event_type, task_id, user_id))

        monkeypatch.setattr("src.routes.tasks.publish_task_event", _fake_publish)

        create_resp = api_client.post("/api/tasks", json={"title": "Delete me"})
        task_id = create_resp.json()["id"]

        del_resp = api_client.delete(f"/api/tasks/{task_id}")
        assert del_resp.status_code == 200

        deleted_events = [p for p in published if p[0] == "task.deleted"]
        assert len(deleted_events) == 1
        assert deleted_events[0][1] == task_id

    def test_update_task_emits_event(
        self, api_client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """PUT /api/tasks/{id} calls publish_task_event('task.updated', ...)."""
        published: list[tuple] = []

        async def _fake_publish(event_type, task_id, user_id, extra=None):
            published.append((event_type, task_id, user_id))

        monkeypatch.setattr("src.routes.tasks.publish_task_event", _fake_publish)

        create_resp = api_client.post("/api/tasks", json={"title": "Original"})
        task_id = create_resp.json()["id"]

        put_resp = api_client.put(
            f"/api/tasks/{task_id}", json={"title": "Updated"}
        )
        assert put_resp.status_code == 200

        updated_events = [p for p in published if p[0] == "task.updated"]
        assert len(updated_events) == 1

    def test_toggle_task_emits_event(
        self, api_client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """PATCH /api/tasks/{id}/toggle calls publish_task_event('task.toggled', ...)."""
        published: list[tuple] = []

        async def _fake_publish(event_type, task_id, user_id, extra=None):
            published.append((event_type, task_id, user_id))

        monkeypatch.setattr("src.routes.tasks.publish_task_event", _fake_publish)

        create_resp = api_client.post("/api/tasks", json={"title": "Toggle me"})
        task_id = create_resp.json()["id"]

        patch_resp = api_client.patch(f"/api/tasks/{task_id}/toggle")
        assert patch_resp.status_code == 200

        toggled_events = [p for p in published if p[0] == "task.toggled"]
        assert len(toggled_events) == 1
