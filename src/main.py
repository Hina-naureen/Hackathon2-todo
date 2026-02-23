# [Task]: T-004
# [From]: specs/phase1-console/plan.md §Entry Point

from src.models import TaskStore
from src.task_service import TaskService
from src.cli import (
    print_menu,
    handle_add,
    handle_view,
    handle_update,
    handle_delete,
    handle_toggle,
)


def main() -> None:
    store = TaskStore()
    service = TaskService(store)

    print("Welcome to Todo App - Phase I")

    while True:
        print_menu()
        choice = input("Enter choice: ").strip()

        if choice == "1":
            handle_add(service)
        elif choice == "2":
            handle_view(service)
        elif choice == "3":
            handle_update(service)
        elif choice == "4":
            handle_delete(service)
        elif choice == "5":
            handle_toggle(service)
        elif choice == "0":
            print("\nGoodbye!")
            break
        else:
            print("Invalid option. Please try again.")


if __name__ == "__main__":
    main()
