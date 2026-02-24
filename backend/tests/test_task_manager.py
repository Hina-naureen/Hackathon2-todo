# tests/test_task_manager.py — unit tests for the service layer
# References: specs/features/task-crud.md §US-01 through §US-05
#             specs/architecture.md §Layer 2 — Service Layer
#
# Naming: test_<unit>_<scenario>_<expected_outcome>
# Each test receives a fresh TaskManager via the conftest fixture.
# No shared state between tests.

from src.task_manager import TaskManager


# ---------------------------------------------------------------------------
# US-01 — Add Task
# ---------------------------------------------------------------------------


class TestAddTask:
    def test_add_task_with_valid_title_returns_task(self, manager: TaskManager) -> None:
        task = manager.add_task("Buy groceries")
        assert task.title == "Buy groceries"

    def test_add_task_first_task_gets_id_one(self, manager: TaskManager) -> None:
        task = manager.add_task("First")
        assert task.id == 1

    def test_add_task_second_task_gets_id_two(self, manager: TaskManager) -> None:
        manager.add_task("First")
        task = manager.add_task("Second")
        assert task.id == 2

    def test_add_task_auto_increments_id_on_each_call(self, manager: TaskManager) -> None:
        ids = [manager.add_task(f"Task {i}").id for i in range(5)]
        assert ids == list(range(1, 6))

    def test_add_task_sets_completed_false_by_default(self, manager: TaskManager) -> None:
        task = manager.add_task("New")
        assert task.completed is False

    def test_add_task_with_no_description_defaults_to_empty_string(
        self, manager: TaskManager
    ) -> None:
        task = manager.add_task("No desc")
        assert task.description == ""

    def test_add_task_stores_given_description(self, manager: TaskManager) -> None:
        task = manager.add_task("Title", "My description")
        assert task.description == "My description"

    def test_add_task_strips_leading_trailing_whitespace_from_title(
        self, manager: TaskManager
    ) -> None:
        task = manager.add_task("  Spaced  ")
        assert task.title == "Spaced"

    def test_add_task_strips_leading_trailing_whitespace_from_description(
        self, manager: TaskManager
    ) -> None:
        task = manager.add_task("Title", "  desc  ")
        assert task.description == "desc"


# ---------------------------------------------------------------------------
# US-02 — List Tasks
# ---------------------------------------------------------------------------


class TestListTasks:
    def test_get_all_tasks_returns_empty_list_when_store_is_empty(
        self, manager: TaskManager
    ) -> None:
        assert manager.get_all_tasks() == []

    def test_get_all_tasks_returns_all_added_tasks(self, manager: TaskManager) -> None:
        manager.add_task("A")
        manager.add_task("B")
        assert len(manager.get_all_tasks()) == 2

    def test_get_all_tasks_returns_tasks_ordered_by_ascending_id(
        self, populated_manager: TaskManager
    ) -> None:
        tasks = populated_manager.get_all_tasks()
        ids = [t.id for t in tasks]
        assert ids == sorted(ids)

    def test_get_all_tasks_returns_tasks_with_correct_titles(
        self, manager: TaskManager
    ) -> None:
        manager.add_task("Alpha")
        manager.add_task("Beta")
        titles = [t.title for t in manager.get_all_tasks()]
        assert "Alpha" in titles
        assert "Beta" in titles

    def test_get_task_returns_correct_task_by_id(self, manager: TaskManager) -> None:
        added = manager.add_task("Find me")
        found = manager.get_task(added.id)
        assert found is not None
        assert found.title == "Find me"

    def test_get_task_returns_none_when_id_not_found(self, manager: TaskManager) -> None:
        assert manager.get_task(999) is None

    def test_get_task_returns_none_on_empty_store(self, manager: TaskManager) -> None:
        assert manager.get_task(1) is None


# ---------------------------------------------------------------------------
# US-03 — Update Task
# ---------------------------------------------------------------------------


class TestUpdateTask:
    def test_update_task_title_changes_the_title(self, manager: TaskManager) -> None:
        task = manager.add_task("Old")
        manager.update_task(task.id, title="New")
        assert manager.get_task(task.id).title == "New"

    def test_update_task_description_changes_the_description(
        self, manager: TaskManager
    ) -> None:
        task = manager.add_task("Title", "old desc")
        manager.update_task(task.id, description="new desc")
        assert manager.get_task(task.id).description == "new desc"

    def test_update_task_with_both_fields_updates_both(self, manager: TaskManager) -> None:
        task = manager.add_task("Old title", "old desc")
        manager.update_task(task.id, title="New title", description="new desc")
        updated = manager.get_task(task.id)
        assert updated.title == "New title"
        assert updated.description == "new desc"

    def test_update_task_with_none_title_keeps_existing_title(
        self, manager: TaskManager
    ) -> None:
        task = manager.add_task("Keep me")
        manager.update_task(task.id, title=None)
        assert manager.get_task(task.id).title == "Keep me"

    def test_update_task_with_none_description_keeps_existing_description(
        self, manager: TaskManager
    ) -> None:
        task = manager.add_task("Title", "Keep this")
        manager.update_task(task.id, description=None)
        assert manager.get_task(task.id).description == "Keep this"

    def test_update_task_with_empty_string_title_keeps_existing_title(
        self, manager: TaskManager
    ) -> None:
        # Empty string after strip is falsy — treated as "no change"
        task = manager.add_task("Keep me")
        manager.update_task(task.id, title="")
        assert manager.get_task(task.id).title == "Keep me"

    def test_update_task_strips_whitespace_from_new_title(
        self, manager: TaskManager
    ) -> None:
        task = manager.add_task("Old")
        manager.update_task(task.id, title="  Trimmed  ")
        assert manager.get_task(task.id).title == "Trimmed"

    def test_update_task_returns_updated_task(self, manager: TaskManager) -> None:
        task = manager.add_task("Title")
        result = manager.update_task(task.id, title="Updated")
        assert result is not None
        assert result.title == "Updated"

    def test_update_task_with_invalid_id_returns_none(self, manager: TaskManager) -> None:
        result = manager.update_task(999, title="New")
        assert result is None

    def test_update_task_does_not_change_completed_flag(
        self, manager: TaskManager
    ) -> None:
        task = manager.add_task("Title")
        manager.toggle_complete(task.id)  # mark complete
        manager.update_task(task.id, title="New title")
        assert manager.get_task(task.id).completed is True

    def test_update_task_does_not_affect_other_tasks(self, manager: TaskManager) -> None:
        t1 = manager.add_task("Task 1", "desc 1")
        t2 = manager.add_task("Task 2", "desc 2")
        manager.update_task(t1.id, title="Changed")
        assert manager.get_task(t2.id).title == "Task 2"


# ---------------------------------------------------------------------------
# US-04 — Delete Task
# ---------------------------------------------------------------------------


class TestDeleteTask:
    def test_delete_task_with_valid_id_returns_true(self, manager: TaskManager) -> None:
        task = manager.add_task("Delete me")
        success, _ = manager.delete_task(task.id)
        assert success is True

    def test_delete_task_returns_task_title_on_success(
        self, manager: TaskManager
    ) -> None:
        task = manager.add_task("My title")
        _, title = manager.delete_task(task.id)
        assert title == "My title"

    def test_delete_task_with_invalid_id_returns_false(
        self, manager: TaskManager
    ) -> None:
        success, title = manager.delete_task(999)
        assert success is False
        assert title == ""

    def test_delete_task_removes_task_from_store(self, manager: TaskManager) -> None:
        task = manager.add_task("Gone")
        manager.delete_task(task.id)
        assert manager.get_task(task.id) is None

    def test_delete_task_reduces_task_count(self, manager: TaskManager) -> None:
        manager.add_task("A")
        task = manager.add_task("B")
        manager.delete_task(task.id)
        assert len(manager.get_all_tasks()) == 1

    def test_delete_task_does_not_affect_other_tasks(self, manager: TaskManager) -> None:
        keep = manager.add_task("Keep")
        drop = manager.add_task("Drop")
        manager.delete_task(drop.id)
        assert manager.get_task(keep.id) is not None

    def test_delete_task_on_empty_store_returns_false(self, manager: TaskManager) -> None:
        success, _ = manager.delete_task(1)
        assert success is False


# ---------------------------------------------------------------------------
# US-05 — Toggle Complete
# ---------------------------------------------------------------------------


class TestToggleComplete:
    def test_toggle_complete_pending_task_marks_as_complete(
        self, manager: TaskManager
    ) -> None:
        task = manager.add_task("Pending")
        assert task.completed is False
        toggled = manager.toggle_complete(task.id)
        assert toggled is not None
        assert toggled.completed is True

    def test_toggle_complete_complete_task_marks_as_pending(
        self, manager: TaskManager
    ) -> None:
        task = manager.add_task("Done")
        manager.toggle_complete(task.id)          # False → True
        toggled = manager.toggle_complete(task.id) # True  → False
        assert toggled is not None
        assert toggled.completed is False

    def test_toggle_complete_with_invalid_id_returns_none(
        self, manager: TaskManager
    ) -> None:
        assert manager.toggle_complete(999) is None

    def test_toggle_complete_returns_updated_task(self, manager: TaskManager) -> None:
        task = manager.add_task("Task")
        result = manager.toggle_complete(task.id)
        assert result is not None
        assert result.id == task.id

    def test_toggle_complete_persists_in_store(self, manager: TaskManager) -> None:
        task = manager.add_task("Task")
        manager.toggle_complete(task.id)
        assert manager.get_task(task.id).completed is True

    def test_toggle_complete_does_not_affect_other_tasks(
        self, manager: TaskManager
    ) -> None:
        t1 = manager.add_task("Task 1")
        t2 = manager.add_task("Task 2")
        manager.toggle_complete(t1.id)
        assert manager.get_task(t2.id).completed is False
