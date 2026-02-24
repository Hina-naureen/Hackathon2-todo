# tests/test_api.py — FastAPI route integration tests (Phase II)
# References: specs/api/rest-endpoints.md
#             specs/database/schema.md §Test Database Strategy
#
# All tests use an in-memory SQLite database via dependency_overrides.
# The AUTH_DISABLED flag is NOT used here — we override get_current_user
# directly so auth behaviour is tested explicitly.

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from src.app import app
from src.auth.dependencies import get_current_user
from src.database import get_session
from src.db_models import Task

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TEST_USER = "user-test-001"
OTHER_USER = "user-test-002"


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


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """TestClient with session + auth overridden for TEST_USER."""

    def _override_session():
        yield session

    def _override_user():
        return TEST_USER

    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[get_current_user] = _override_user
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def _seed_other_task(session: Session, title: str = "Other task") -> Task:
    """Insert a task owned by OTHER_USER directly into the DB (no client needed)."""
    task = Task(title=title, user_id=OTHER_USER)
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


class TestHealth:
    def test_health_returns_ok(self, client: TestClient):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# GET /api/tasks
# ---------------------------------------------------------------------------


class TestListTasks:
    def test_empty_list_returns_200(self, client: TestClient):
        r = client.get("/api/tasks")
        assert r.status_code == 200
        assert r.json() == []

    def test_returns_only_own_tasks(self, client: TestClient, session: Session):
        client.post("/api/tasks", json={"title": "My task"})
        _seed_other_task(session, "Other task")   # direct DB insert, no client conflict

        r = client.get("/api/tasks")
        titles = [t["title"] for t in r.json()]
        assert "My task" in titles
        assert "Other task" not in titles

    def test_tasks_ordered_by_id_ascending(self, client: TestClient):
        client.post("/api/tasks", json={"title": "First"})
        client.post("/api/tasks", json={"title": "Second"})
        client.post("/api/tasks", json={"title": "Third"})

        tasks = client.get("/api/tasks").json()
        ids = [t["id"] for t in tasks]
        assert ids == sorted(ids)

    def test_returns_all_fields(self, client: TestClient):
        client.post("/api/tasks", json={"title": "T", "description": "D"})
        task = client.get("/api/tasks").json()[0]
        assert {"id", "title", "description", "completed", "created_at", "updated_at"} <= task.keys()
        assert "user_id" not in task


# ---------------------------------------------------------------------------
# POST /api/tasks
# ---------------------------------------------------------------------------


class TestCreateTask:
    def test_valid_task_returns_201(self, client: TestClient):
        r = client.post("/api/tasks", json={"title": "Buy milk"})
        assert r.status_code == 201

    def test_response_has_correct_fields(self, client: TestClient):
        r = client.post("/api/tasks", json={"title": "Buy milk", "description": "2 litres"})
        data = r.json()
        assert data["title"] == "Buy milk"
        assert data["description"] == "2 litres"
        assert data["completed"] is False
        assert data["id"] is not None

    def test_description_defaults_to_empty_string(self, client: TestClient):
        r = client.post("/api/tasks", json={"title": "No desc"})
        assert r.json()["description"] == ""

    def test_title_is_stripped(self, client: TestClient):
        r = client.post("/api/tasks", json={"title": "  spaced  "})
        assert r.json()["title"] == "spaced"

    def test_empty_title_returns_400(self, client: TestClient):
        r = client.post("/api/tasks", json={"title": ""})
        assert r.status_code == 400
        assert "empty" in r.json()["detail"].lower()

    def test_whitespace_title_returns_400(self, client: TestClient):
        r = client.post("/api/tasks", json={"title": "   "})
        assert r.status_code == 400

    def test_title_too_long_returns_400(self, client: TestClient):
        r = client.post("/api/tasks", json={"title": "x" * 201})
        assert r.status_code == 400
        assert "200" in r.json()["detail"]

    def test_description_too_long_returns_400(self, client: TestClient):
        r = client.post("/api/tasks", json={"title": "ok", "description": "x" * 501})
        assert r.status_code == 400
        assert "500" in r.json()["detail"]

    def test_ids_are_unique_and_incrementing(self, client: TestClient):
        id1 = client.post("/api/tasks", json={"title": "A"}).json()["id"]
        id2 = client.post("/api/tasks", json={"title": "B"}).json()["id"]
        assert id2 > id1


# ---------------------------------------------------------------------------
# GET /api/tasks/{task_id}
# ---------------------------------------------------------------------------


class TestGetTask:
    def test_existing_task_returns_200(self, client: TestClient):
        task_id = client.post("/api/tasks", json={"title": "Find me"}).json()["id"]
        r = client.get(f"/api/tasks/{task_id}")
        assert r.status_code == 200
        assert r.json()["title"] == "Find me"

    def test_nonexistent_task_returns_404(self, client: TestClient):
        r = client.get("/api/tasks/9999")
        assert r.status_code == 404
        assert "not found" in r.json()["detail"].lower()

    def test_other_users_task_returns_404(self, client: TestClient, session: Session):
        other = _seed_other_task(session, "Private")
        r = client.get(f"/api/tasks/{other.id}")
        assert r.status_code == 404  # 404, not 403 — no information leakage


# ---------------------------------------------------------------------------
# PUT /api/tasks/{task_id}
# ---------------------------------------------------------------------------


class TestUpdateTask:
    def _create(self, client: TestClient, title: str = "Original", desc: str = "Desc") -> int:
        return client.post("/api/tasks", json={"title": title, "description": desc}).json()["id"]

    def test_update_title_returns_200(self, client: TestClient):
        tid = self._create(client)
        r = client.put(f"/api/tasks/{tid}", json={"title": "Updated"})
        assert r.status_code == 200
        assert r.json()["title"] == "Updated"

    def test_null_title_keeps_existing(self, client: TestClient):
        tid = self._create(client, title="Keep me")
        r = client.put(f"/api/tasks/{tid}", json={"title": None})
        assert r.json()["title"] == "Keep me"

    def test_null_description_keeps_existing(self, client: TestClient):
        tid = self._create(client, desc="Keep desc")
        r = client.put(f"/api/tasks/{tid}", json={"description": None})
        assert r.json()["description"] == "Keep desc"

    def test_empty_string_clears_description(self, client: TestClient):
        tid = self._create(client, desc="Has content")
        r = client.put(f"/api/tasks/{tid}", json={"description": ""})
        assert r.json()["description"] == ""

    def test_empty_string_title_returns_400(self, client: TestClient):
        tid = self._create(client)
        r = client.put(f"/api/tasks/{tid}", json={"title": ""})
        assert r.status_code == 400

    def test_title_too_long_returns_400(self, client: TestClient):
        tid = self._create(client)
        r = client.put(f"/api/tasks/{tid}", json={"title": "x" * 201})
        assert r.status_code == 400

    def test_nonexistent_task_returns_404(self, client: TestClient):
        r = client.put("/api/tasks/9999", json={"title": "Ghost"})
        assert r.status_code == 404

    def test_updated_at_changes(self, client: TestClient):
        tid = self._create(client)
        before = client.get(f"/api/tasks/{tid}").json()["updated_at"]
        import time; time.sleep(0.01)
        client.put(f"/api/tasks/{tid}", json={"title": "New"})
        after = client.get(f"/api/tasks/{tid}").json()["updated_at"]
        assert after >= before


# ---------------------------------------------------------------------------
# DELETE /api/tasks/{task_id}
# ---------------------------------------------------------------------------


class TestDeleteTask:
    def test_delete_returns_200_with_message(self, client: TestClient):
        tid = client.post("/api/tasks", json={"title": "Gone"}).json()["id"]
        r = client.delete(f"/api/tasks/{tid}")
        assert r.status_code == 200
        assert str(tid) in r.json()["detail"]

    def test_deleted_task_no_longer_in_list(self, client: TestClient):
        tid = client.post("/api/tasks", json={"title": "Gone"}).json()["id"]
        client.delete(f"/api/tasks/{tid}")
        ids = [t["id"] for t in client.get("/api/tasks").json()]
        assert tid not in ids

    def test_double_delete_returns_404(self, client: TestClient):
        tid = client.post("/api/tasks", json={"title": "Gone"}).json()["id"]
        client.delete(f"/api/tasks/{tid}")
        r = client.delete(f"/api/tasks/{tid}")
        assert r.status_code == 404

    def test_nonexistent_task_returns_404(self, client: TestClient):
        r = client.delete("/api/tasks/9999")
        assert r.status_code == 404

    def test_other_users_task_not_deleted(self, client: TestClient, session: Session):
        other = _seed_other_task(session, "Protected")
        r = client.delete(f"/api/tasks/{other.id}")
        assert r.status_code == 404
        # Still exists in the DB
        session.refresh(other)
        assert other.id is not None


# ---------------------------------------------------------------------------
# PATCH /api/tasks/{task_id}/toggle
# ---------------------------------------------------------------------------


class TestToggleTask:
    def test_pending_becomes_complete(self, client: TestClient):
        tid = client.post("/api/tasks", json={"title": "Todo"}).json()["id"]
        r = client.patch(f"/api/tasks/{tid}/toggle")
        assert r.status_code == 200
        assert r.json()["completed"] is True

    def test_complete_becomes_pending(self, client: TestClient):
        tid = client.post("/api/tasks", json={"title": "Todo"}).json()["id"]
        client.patch(f"/api/tasks/{tid}/toggle")       # → complete
        r = client.patch(f"/api/tasks/{tid}/toggle")   # → pending
        assert r.json()["completed"] is False

    def test_double_toggle_restores_original(self, client: TestClient):
        tid = client.post("/api/tasks", json={"title": "Todo"}).json()["id"]
        client.patch(f"/api/tasks/{tid}/toggle")
        client.patch(f"/api/tasks/{tid}/toggle")
        assert client.get(f"/api/tasks/{tid}").json()["completed"] is False

    def test_nonexistent_task_returns_404(self, client: TestClient):
        r = client.patch("/api/tasks/9999/toggle")
        assert r.status_code == 404

    def test_updated_at_changes_after_toggle(self, client: TestClient):
        tid = client.post("/api/tasks", json={"title": "T"}).json()["id"]
        before = client.get(f"/api/tasks/{tid}").json()["updated_at"]
        import time; time.sleep(0.01)
        client.patch(f"/api/tasks/{tid}/toggle")
        after = client.get(f"/api/tasks/{tid}").json()["updated_at"]
        assert after >= before


# ---------------------------------------------------------------------------
# Auth — 401 behaviour (no AUTH_DISABLED override)
# ---------------------------------------------------------------------------


class TestAuth:
    def test_missing_token_returns_401(self):
        """Ensure unauthenticated requests are rejected when overrides are cleared."""
        app.dependency_overrides.clear()
        with TestClient(app) as bare_client:
            r = bare_client.get("/api/tasks")
        assert r.status_code == 401
        assert r.json()["detail"] == "Not authenticated."

    def test_invalid_token_returns_401(self):
        app.dependency_overrides.clear()
        with TestClient(app) as bare_client:
            r = bare_client.get(
                "/api/tasks",
                headers={"Authorization": "Bearer not-a-real-jwt"},
            )
        assert r.status_code == 401
