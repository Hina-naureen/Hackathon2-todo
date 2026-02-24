# tests/test_models.py — unit tests for the data layer
# References: specs/features/task-crud.md §Key Entities
#             specs/architecture.md §Layer 1 — Data Layer
#
# Naming: test_<unit>_<scenario>_<expected_outcome>
# Each test gets a fresh TaskStore via the conftest fixture.

from src.models import (
    Task,
    TaskStore,
    MAX_TITLE_LENGTH,
    MAX_DESCRIPTION_LENGTH,
    STATUS_COMPLETE,
    STATUS_PENDING,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestConstants:
    def test_max_title_length_is_200(self) -> None:
        assert MAX_TITLE_LENGTH == 200

    def test_max_description_length_is_500(self) -> None:
        assert MAX_DESCRIPTION_LENGTH == 500

    def test_status_complete_and_pending_are_different(self) -> None:
        assert STATUS_COMPLETE != STATUS_PENDING

    def test_status_icons_are_strings(self) -> None:
        assert isinstance(STATUS_COMPLETE, str)
        assert isinstance(STATUS_PENDING, str)


# ---------------------------------------------------------------------------
# Task dataclass
# ---------------------------------------------------------------------------


class TestTask:
    def test_task_stores_id(self) -> None:
        task = Task(id=7, title="Test")
        assert task.id == 7

    def test_task_stores_title(self) -> None:
        task = Task(id=1, title="My title")
        assert task.title == "My title"

    def test_task_defaults_description_to_empty_string(self) -> None:
        task = Task(id=1, title="No desc")
        assert task.description == ""

    def test_task_defaults_completed_to_false(self) -> None:
        task = Task(id=1, title="Not done")
        assert task.completed is False

    def test_task_stores_explicit_description(self) -> None:
        task = Task(id=1, title="T", description="my desc")
        assert task.description == "my desc"

    def test_task_stores_explicit_completed_true(self) -> None:
        task = Task(id=1, title="T", completed=True)
        assert task.completed is True


# ---------------------------------------------------------------------------
# TaskStore — add
# ---------------------------------------------------------------------------


class TestTaskStoreAdd:
    def test_add_first_task_assigns_id_one(self, store: TaskStore) -> None:
        task = store.add("First")
        assert task.id == 1

    def test_add_second_task_assigns_id_two(self, store: TaskStore) -> None:
        store.add("First")
        task = store.add("Second")
        assert task.id == 2

    def test_add_returns_task_with_correct_title(self, store: TaskStore) -> None:
        task = store.add("Buy milk")
        assert task.title == "Buy milk"

    def test_add_returns_task_with_correct_description(self, store: TaskStore) -> None:
        task = store.add("Title", "My desc")
        assert task.description == "My desc"

    def test_add_defaults_completed_to_false(self, store: TaskStore) -> None:
        task = store.add("New task")
        assert task.completed is False

    def test_add_id_does_not_reuse_deleted_id(self, store: TaskStore) -> None:
        t1 = store.add("First")
        store.delete(t1.id)
        t2 = store.add("Second")
        assert t2.id == 2  # continues from counter, does not reuse 1

    def test_add_multiple_tasks_each_get_unique_id(self, store: TaskStore) -> None:
        ids = [store.add(f"Task {i}").id for i in range(5)]
        assert len(set(ids)) == 5  # all unique


# ---------------------------------------------------------------------------
# TaskStore — get_all
# ---------------------------------------------------------------------------


class TestTaskStoreGetAll:
    def test_get_all_returns_empty_list_on_empty_store(self, store: TaskStore) -> None:
        assert store.get_all() == []

    def test_get_all_returns_all_added_tasks(self, store: TaskStore) -> None:
        store.add("A")
        store.add("B")
        store.add("C")
        assert len(store.get_all()) == 3

    def test_get_all_returns_tasks_in_ascending_id_order(self, store: TaskStore) -> None:
        store.add("A")
        store.add("B")
        store.add("C")
        ids = [t.id for t in store.get_all()]
        assert ids == sorted(ids)

    def test_get_all_returns_shallow_copy_not_internal_list(self, store: TaskStore) -> None:
        store.add("Task")
        result = store.get_all()
        result.clear()                    # mutate the returned list
        assert len(store.get_all()) == 1  # store is unaffected


# ---------------------------------------------------------------------------
# TaskStore — get_by_id
# ---------------------------------------------------------------------------


class TestTaskStoreGetById:
    def test_get_by_id_returns_task_when_found(self, store: TaskStore) -> None:
        added = store.add("Find me")
        found = store.get_by_id(added.id)
        assert found is not None
        assert found.id == added.id

    def test_get_by_id_returns_correct_task_among_many(self, store: TaskStore) -> None:
        store.add("One")
        target = store.add("Two")
        store.add("Three")
        found = store.get_by_id(target.id)
        assert found is not None
        assert found.title == "Two"

    def test_get_by_id_returns_none_when_id_missing(self, store: TaskStore) -> None:
        assert store.get_by_id(999) is None

    def test_get_by_id_returns_none_on_empty_store(self, store: TaskStore) -> None:
        assert store.get_by_id(1) is None


# ---------------------------------------------------------------------------
# TaskStore — delete
# ---------------------------------------------------------------------------


class TestTaskStoreDelete:
    def test_delete_returns_true_when_task_exists(self, store: TaskStore) -> None:
        task = store.add("Delete me")
        assert store.delete(task.id) is True

    def test_delete_returns_false_when_id_not_found(self, store: TaskStore) -> None:
        assert store.delete(999) is False

    def test_delete_removes_task_from_store(self, store: TaskStore) -> None:
        task = store.add("Gone")
        store.delete(task.id)
        assert store.get_by_id(task.id) is None

    def test_delete_reduces_task_count_by_one(self, store: TaskStore) -> None:
        store.add("A")
        t = store.add("B")
        store.delete(t.id)
        assert len(store.get_all()) == 1

    def test_delete_does_not_affect_other_tasks(self, store: TaskStore) -> None:
        keep = store.add("Keep")
        drop = store.add("Drop")
        store.delete(drop.id)
        assert store.get_by_id(keep.id) is not None

    def test_delete_same_id_twice_returns_false_on_second_call(self, store: TaskStore) -> None:
        task = store.add("Once")
        store.delete(task.id)
        assert store.delete(task.id) is False
