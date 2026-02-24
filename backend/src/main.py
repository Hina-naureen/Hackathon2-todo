# src/main.py — Entry point
# References: specs/architecture.md §Entry Point
#             specs/constitution.md §VII Error Handling Contract
#             specs/features/task-crud.md §Edge Cases (KeyboardInterrupt)

import sys

from src.models import TaskStore
from src.task_manager import TaskManager
from src.cli import (
    print_menu,
    handle_add,
    handle_view,
    handle_update,
    handle_delete,
    handle_toggle,
)


def main() -> None:
    """Bootstrap the application and run the main event loop.

    Responsibilities (and nothing else):
      - Instantiate TaskStore and inject it into TaskManager.
      - Render the menu and route each choice to the correct handler.
      - Handle KeyboardInterrupt (Ctrl+C) with a clean exit message.
      - Catch unexpected exceptions without exposing a traceback to the user.
    """
    store = TaskStore()
    manager = TaskManager(store)

    print("\n  Todo App  -  Phase I  |  Press Ctrl+C to exit")

    while True:
        try:
            print_menu()
            choice = input("  Enter choice [0-5]   : ").strip()

            if choice == "1":
                handle_add(manager)
            elif choice == "2":
                handle_view(manager)
            elif choice == "3":
                handle_update(manager)
            elif choice == "4":
                handle_delete(manager)
            elif choice == "5":
                handle_toggle(manager)
            elif choice == "0":
                print("\n  Goodbye!")
                break
            else:
                print("  Invalid option. Please try again.")

        except KeyboardInterrupt:
            # spec §Edge Cases: Ctrl+C must exit cleanly with no traceback
            print("\n  Goodbye!")
            sys.exit(0)

        except Exception as exc:  # noqa: BLE001
            # constitution §VII: unexpected errors surface a message, not a traceback
            print(f"  Error: {exc}. Please try again.")


if __name__ == "__main__":
    main()
