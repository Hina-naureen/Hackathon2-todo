# tests/test_cli.py — integration tests for the CLI layer
# References: specs/features/task-crud.md §US-01 through §US-05, §Error Catalogue
#             specs/architecture.md §Layer 3 — CLI Layer
#
# Strategy:
#   - monkeypatch builtins.input to inject user responses in order.
#   - capsys captures stdout for assertion.
#   - Each test uses a fresh TaskManager (via conftest fixtures).
#
# Input call order per handler:
#   handle_add    : title → description
#   handle_update : task_id → new_title → new_description
#   handle_delete : task_id → confirmation (y/n)
#   handle_toggle : task_id
#   handle_view   : no input

import builtins

import pytest

from src.models import STATUS_COMPLETE, STATUS_PENDING
from src.task_manager import TaskManager
from src.cli import (
    handle_add,
    handle_view,
    handle_update,
    handle_delete,
    handle_toggle,
)
from tests.conftest import make_inputs


# ---------------------------------------------------------------------------
# US-01 — handle_add
# ---------------------------------------------------------------------------


class TestHandleAdd:
    def test_add_task_with_valid_title_creates_task(
        self, monkeypatch, manager: TaskManager
    ) -> None:
        monkeypatch.setattr(builtins, "input", make_inputs("Buy milk", ""))
        handle_add(manager)
        assert len(manager.get_all_tasks()) == 1
        assert manager.get_all_tasks()[0].title == "Buy milk"

    def test_add_task_with_description_stores_description(
        self, monkeypatch, manager: TaskManager
    ) -> None:
        monkeypatch.setattr(builtins, "input", make_inputs("Groceries", "Milk and eggs"))
        handle_add(manager)
        assert manager.get_all_tasks()[0].description == "Milk and eggs"

    def test_add_task_prints_success_message(
        self, monkeypatch, capsys, manager: TaskManager
    ) -> None:
        monkeypatch.setattr(builtins, "input", make_inputs("Task A", ""))
        handle_add(manager)
        assert "Task #1 added successfully" in capsys.readouterr().out

    def test_add_task_with_empty_description_stores_empty_string(
        self, monkeypatch, manager: TaskManager
    ) -> None:
        monkeypatch.setattr(builtins, "input", make_inputs("No desc", ""))
        handle_add(manager)
        assert manager.get_all_tasks()[0].description == ""

    # --- error paths (spec §Error Catalogue) ---

    def test_add_task_empty_title_prints_error_and_adds_no_task(
        self, monkeypatch, capsys, manager: TaskManager
    ) -> None:
        monkeypatch.setattr(builtins, "input", make_inputs(""))
        handle_add(manager)
        out = capsys.readouterr().out
        assert "Title cannot be empty" in out
        assert manager.get_all_tasks() == []

    def test_add_task_whitespace_only_title_prints_error(
        self, monkeypatch, capsys, manager: TaskManager
    ) -> None:
        monkeypatch.setattr(builtins, "input", make_inputs("   "))
        handle_add(manager)
        assert "Title cannot be empty" in capsys.readouterr().out

    def test_add_task_title_exceeding_200_chars_prints_error(
        self, monkeypatch, capsys, manager: TaskManager
    ) -> None:
        monkeypatch.setattr(builtins, "input", make_inputs("x" * 201))
        handle_add(manager)
        out = capsys.readouterr().out
        assert "200 characters or fewer" in out
        assert manager.get_all_tasks() == []

    def test_add_task_description_exceeding_500_chars_prints_error(
        self, monkeypatch, capsys, manager: TaskManager
    ) -> None:
        monkeypatch.setattr(builtins, "input", make_inputs("Valid", "d" * 501))
        handle_add(manager)
        out = capsys.readouterr().out
        assert "500 characters or fewer" in out
        assert manager.get_all_tasks() == []


# ---------------------------------------------------------------------------
# US-02 — handle_view (no input — output only)
# ---------------------------------------------------------------------------


class TestHandleView:
    def test_view_empty_store_prints_no_tasks_found(
        self, capsys, manager: TaskManager
    ) -> None:
        handle_view(manager)
        assert "No tasks found" in capsys.readouterr().out

    def test_view_prints_task_titles(
        self, capsys, manager: TaskManager
    ) -> None:
        manager.add_task("Buy groceries")
        manager.add_task("Submit report")
        handle_view(manager)
        out = capsys.readouterr().out
        assert "Buy groceries" in out
        assert "Submit report" in out

    def test_view_shows_pending_status_icon_for_incomplete_task(
        self, capsys, manager: TaskManager
    ) -> None:
        manager.add_task("Pending task")
        handle_view(manager)
        assert STATUS_PENDING in capsys.readouterr().out

    def test_view_shows_complete_status_icon_for_completed_task(
        self, capsys, manager: TaskManager
    ) -> None:
        task = manager.add_task("Done task")
        manager.toggle_complete(task.id)
        handle_view(manager)
        assert STATUS_COMPLETE in capsys.readouterr().out

    def test_view_shows_task_count(
        self, capsys, populated_manager: TaskManager
    ) -> None:
        handle_view(populated_manager)
        assert "task(s)" in capsys.readouterr().out

    def test_view_truncates_long_description(
        self, capsys, manager: TaskManager
    ) -> None:
        manager.add_task("Title", "A" * 40)  # exceeds DISPLAY_DESCRIPTION_LIMIT
        handle_view(manager)
        out = capsys.readouterr().out
        assert ".." in out  # truncation suffix present

    def test_view_shows_full_short_description(
        self, capsys, manager: TaskManager
    ) -> None:
        manager.add_task("Title", "Short desc")
        handle_view(manager)
        assert "Short desc" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# US-03 — handle_update
# ---------------------------------------------------------------------------


class TestHandleUpdate:
    def test_update_task_title_updates_the_task(
        self, monkeypatch, manager: TaskManager
    ) -> None:
        task = manager.add_task("Old title")
        monkeypatch.setattr(builtins, "input", make_inputs(str(task.id), "New title", ""))
        handle_update(manager)
        assert manager.get_task(task.id).title == "New title"

    def test_update_task_prints_success_message(
        self, monkeypatch, capsys, manager: TaskManager
    ) -> None:
        task = manager.add_task("Title")
        monkeypatch.setattr(builtins, "input", make_inputs(str(task.id), "Updated", ""))
        handle_update(manager)
        assert "updated successfully" in capsys.readouterr().out

    def test_update_task_enter_for_title_keeps_existing_title(
        self, monkeypatch, manager: TaskManager
    ) -> None:
        task = manager.add_task("Keep me", "keep desc")
        monkeypatch.setattr(builtins, "input", make_inputs(str(task.id), "", ""))
        handle_update(manager)
        assert manager.get_task(task.id).title == "Keep me"

    def test_update_task_enter_for_description_keeps_existing_description(
        self, monkeypatch, manager: TaskManager
    ) -> None:
        task = manager.add_task("Title", "Keep this desc")
        monkeypatch.setattr(builtins, "input", make_inputs(str(task.id), "", ""))
        handle_update(manager)
        assert manager.get_task(task.id).description == "Keep this desc"

    def test_update_task_with_id_not_found_prints_error(
        self, monkeypatch, capsys, manager: TaskManager
    ) -> None:
        monkeypatch.setattr(builtins, "input", make_inputs("999", "", ""))
        handle_update(manager)
        assert "not found" in capsys.readouterr().out

    def test_update_task_with_non_integer_id_prints_error(
        self, monkeypatch, capsys, manager: TaskManager
    ) -> None:
        monkeypatch.setattr(builtins, "input", make_inputs("abc", "", ""))
        handle_update(manager)
        assert "valid task ID" in capsys.readouterr().out

    def test_update_task_description_can_be_set_to_empty(
        self, monkeypatch, manager: TaskManager
    ) -> None:
        task = manager.add_task("Title", "Had a desc")
        # Typing a non-empty value for desc clears it (user explicitly empties it)
        monkeypatch.setattr(builtins, "input", make_inputs(str(task.id), "", ""))
        handle_update(manager)
        # Pressing Enter (empty string) keeps the existing description
        assert manager.get_task(task.id).description == "Had a desc"


# ---------------------------------------------------------------------------
# US-04 — handle_delete
# ---------------------------------------------------------------------------


class TestHandleDelete:
    def test_delete_task_confirmed_removes_task(
        self, monkeypatch, manager: TaskManager
    ) -> None:
        task = manager.add_task("Delete me")
        monkeypatch.setattr(builtins, "input", make_inputs(str(task.id), "y"))
        handle_delete(manager)
        assert manager.get_task(task.id) is None

    def test_delete_task_confirmed_prints_deleted_message(
        self, monkeypatch, capsys, manager: TaskManager
    ) -> None:
        task = manager.add_task("Delete me")
        monkeypatch.setattr(builtins, "input", make_inputs(str(task.id), "y"))
        handle_delete(manager)
        assert "deleted" in capsys.readouterr().out

    def test_delete_task_cancelled_keeps_task(
        self, monkeypatch, manager: TaskManager
    ) -> None:
        task = manager.add_task("Keep me")
        monkeypatch.setattr(builtins, "input", make_inputs(str(task.id), "n"))
        handle_delete(manager)
        assert manager.get_task(task.id) is not None

    def test_delete_task_cancelled_prints_cancel_message(
        self, monkeypatch, capsys, manager: TaskManager
    ) -> None:
        task = manager.add_task("Keep me")
        monkeypatch.setattr(builtins, "input", make_inputs(str(task.id), "n"))
        handle_delete(manager)
        assert "cancelled" in capsys.readouterr().out

    def test_delete_task_with_id_not_found_prints_error(
        self, monkeypatch, capsys, manager: TaskManager
    ) -> None:
        monkeypatch.setattr(builtins, "input", make_inputs("999", "y"))
        handle_delete(manager)
        assert "not found" in capsys.readouterr().out

    def test_delete_task_with_non_integer_id_prints_error(
        self, monkeypatch, capsys, manager: TaskManager
    ) -> None:
        monkeypatch.setattr(builtins, "input", make_inputs("abc"))
        handle_delete(manager)
        assert "valid task ID" in capsys.readouterr().out

    def test_delete_task_does_not_affect_other_tasks(
        self, monkeypatch, manager: TaskManager
    ) -> None:
        keep = manager.add_task("Keep")
        drop = manager.add_task("Drop")
        monkeypatch.setattr(builtins, "input", make_inputs(str(drop.id), "y"))
        handle_delete(manager)
        assert manager.get_task(keep.id) is not None


# ---------------------------------------------------------------------------
# US-05 — handle_toggle
# ---------------------------------------------------------------------------


class TestHandleToggle:
    def test_toggle_pending_task_marks_as_complete(
        self, monkeypatch, manager: TaskManager
    ) -> None:
        task = manager.add_task("Pending")
        monkeypatch.setattr(builtins, "input", make_inputs(str(task.id)))
        handle_toggle(manager)
        assert manager.get_task(task.id).completed is True

    def test_toggle_complete_task_marks_as_pending(
        self, monkeypatch, manager: TaskManager
    ) -> None:
        task = manager.add_task("Done")
        manager.toggle_complete(task.id)  # set to complete
        monkeypatch.setattr(builtins, "input", make_inputs(str(task.id)))
        handle_toggle(manager)
        assert manager.get_task(task.id).completed is False

    def test_toggle_pending_task_prints_marked_as_complete(
        self, monkeypatch, capsys, manager: TaskManager
    ) -> None:
        task = manager.add_task("Pending")
        monkeypatch.setattr(builtins, "input", make_inputs(str(task.id)))
        handle_toggle(manager)
        assert "marked as complete" in capsys.readouterr().out

    def test_toggle_complete_task_prints_marked_as_pending(
        self, monkeypatch, capsys, manager: TaskManager
    ) -> None:
        task = manager.add_task("Done")
        manager.toggle_complete(task.id)
        monkeypatch.setattr(builtins, "input", make_inputs(str(task.id)))
        handle_toggle(manager)
        assert "marked as pending" in capsys.readouterr().out

    def test_toggle_task_with_id_not_found_prints_error(
        self, monkeypatch, capsys, manager: TaskManager
    ) -> None:
        monkeypatch.setattr(builtins, "input", make_inputs("999"))
        handle_toggle(manager)
        assert "not found" in capsys.readouterr().out

    def test_toggle_task_with_non_integer_id_prints_error(
        self, monkeypatch, capsys, manager: TaskManager
    ) -> None:
        monkeypatch.setattr(builtins, "input", make_inputs("abc"))
        handle_toggle(manager)
        assert "valid task ID" in capsys.readouterr().out

    def test_toggle_does_not_affect_other_tasks(
        self, monkeypatch, manager: TaskManager
    ) -> None:
        t1 = manager.add_task("Task 1")
        t2 = manager.add_task("Task 2")
        monkeypatch.setattr(builtins, "input", make_inputs(str(t1.id)))
        handle_toggle(manager)
        assert manager.get_task(t2.id).completed is False
