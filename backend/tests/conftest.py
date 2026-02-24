# tests/conftest.py — shared pytest fixtures
# References: specs/constitution.md §V Testing Philosophy
#             specs/architecture.md §Testing Architecture
#
# Isolation rule: every fixture creates a brand-new TaskStore.
# No shared mutable state between tests.

import builtins
from collections.abc import Iterator
from typing import Any

import pytest

from src.models import TaskStore
from src.task_manager import TaskManager


# ---------------------------------------------------------------------------
# Store / manager fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def store() -> TaskStore:
    """Fresh in-memory TaskStore — zero tasks, ID counter at 1."""
    return TaskStore()


@pytest.fixture
def manager(store: TaskStore) -> TaskManager:
    """TaskManager wired to a fresh store."""
    return TaskManager(store)


@pytest.fixture
def populated_manager(manager: TaskManager) -> TaskManager:
    """TaskManager pre-loaded with three tasks for view/list tests."""
    manager.add_task("Buy groceries", "Milk and eggs")
    manager.add_task("Submit report")
    manager.add_task("Exercise", "30 minutes cardio")
    return manager


# ---------------------------------------------------------------------------
# Input-mocking helper
# ---------------------------------------------------------------------------


def make_inputs(*responses: str):
    """Return an input() mock that yields *responses in order.

    Usage::

        monkeypatch.setattr(builtins, "input", make_inputs("Title", "Desc"))

    Each call to the mock consumes the next response.
    The prompt argument passed by callers is accepted but ignored,
    which matches the real builtins.input() signature.
    """
    it: Iterator[str] = iter(responses)

    def _mock_input(prompt: Any = "") -> str:
        return next(it)

    return _mock_input
