# Phase I Spec: In-Memory Python Console Todo App

## Overview
Build a command-line todo application that stores tasks in memory using Python 3.13+ and UV. No database, no persistence — data lives in RAM only.

## Technology Stack
- Python 3.13+
- UV package manager
- No external dependencies (stdlib only)

## User Stories

### US-01: Add a Task
As a user, I want to add a new task with a title and optional description, so I can track things I need to do.

**Acceptance Criteria:**
- User can enter a task title (required, 1-200 characters)
- User can enter a task description (optional, max 500 characters)
- Each task gets a unique auto-incremented integer ID
- Task is created with status "pending" by default
- System confirms: "Task #<id> added successfully."
- Empty title is rejected with error message

### US-02: View All Tasks
As a user, I want to see all my tasks in a formatted list, so I can know what I need to do.

**Acceptance Criteria:**
- All tasks displayed in a table format
- Shows: ID, Title, Description (truncated to 30 chars), Status
- Status shown as "[✓] Complete" or "[ ] Pending"
- If no tasks exist, shows: "No tasks found."
- Tasks ordered by ID (ascending)

### US-03: Update a Task
As a user, I want to update the title or description of an existing task, so I can correct or improve it.

**Acceptance Criteria:**
- User provides task ID to update
- User can update title, description, or both
- Pressing Enter without input keeps existing value
- System confirms: "Task #<id> updated successfully."
- Invalid ID shows error: "Task #<id> not found."

### US-04: Delete a Task
As a user, I want to delete a task by its ID, so I can remove tasks I no longer need.

**Acceptance Criteria:**
- User provides task ID to delete
- System asks for confirmation: "Delete task '<title>'? (y/n):"
- On 'y': task removed, confirms "Task #<id> deleted."
- On 'n': cancels, shows "Delete cancelled."
- Invalid ID shows error: "Task #<id> not found."

### US-05: Mark Task Complete / Incomplete
As a user, I want to toggle a task's completion status, so I can track progress.

**Acceptance Criteria:**
- User provides task ID
- If pending → marks complete, shows "Task #<id> marked as complete."
- If complete → marks pending, shows "Task #<id> marked as pending."
- Invalid ID shows error: "Task #<id> not found."

## Data Model

```python
Task:
  id: int           # Auto-incremented, starts at 1
  title: str        # Required, 1-200 chars
  description: str  # Optional, default ""
  completed: bool   # Default False
```

## Application Flow

```
=== Todo App ===

1. Add Task
2. View Tasks
3. Update Task
4. Delete Task
5. Toggle Complete
0. Exit

Enter choice:
```

## Error Handling
- Invalid menu choice: "Invalid option. Please try again."
- Non-integer ID input: "Please enter a valid task ID."
- Empty required fields: "Title cannot be empty."

## Out of Scope (Phase I)
- No file/database persistence
- No sorting or filtering
- No priorities or tags
- No due dates
- No authentication
- No web interface
