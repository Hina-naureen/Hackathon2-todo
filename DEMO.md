# Demo Script — Phase I Console Todo App
## 90-Second Walkthrough

**Run command:** `uv run todo`
**Terminal:** Windows Terminal or any 80-col console
**Font size:** 14–16 px for legibility on screen recording

---

## Setup Before Recording

Clear the terminal, then start fresh:

```bash
cls
uv run todo
```

---

## Script

---

### [0:00 – 0:06] LAUNCH

**Action:** Type and press Enter

```
uv run todo
```

**Screen shows:**

```
  Todo App  -  Phase I  |  Press Ctrl+C to exit

  +--------------------------------------------+
  |            TODO APP  -  PHASE I            |
  +--------------------------------------------+
  |                                            |
  |  [1]  Add Task                             |
  |  [2]  View All Tasks                       |
  |  [3]  Update Task                          |
  |  [4]  Delete Task                          |
  |  [5]  Toggle Complete / Incomplete         |
  |  [0]  Exit                                 |
  |                                            |
  +--------------------------------------------+
  Enter choice [0-5]   :
```

**Narration:** *"Phase I — a fully spec-driven Python console todo app, zero dependencies, built entirely by Claude Code from formal specifications."*

---

### [0:06 – 0:24] FEATURE 1 — ADD TASK

**Action:** Press `1` → Enter

```
  >> Add New Task
  --------------------------------------------
  Title (required)     :
```

**Action:** Type title → Enter → Type description → Enter

```
  Title (required)     : Prepare demo slides
  Description          : Hackathon II presentation
  Task #1 added successfully.
```

**Action:** Press `1` again → add second task

```
  Title (required)     : Write project README
  Description          :               ← (press Enter, no description)
  Task #2 added successfully.
```

**Action:** Press `1` again → add third task

```
  Title (required)     : Push code to GitHub
  Description          :               ← (press Enter)
  Task #3 added successfully.
```

**Narration:** *"Add tasks with a required title and optional description. Each gets a unique auto-incremented ID."*

---

### [0:24 – 0:36] FEATURE 2 — VIEW TASKS

**Action:** Press `2` → Enter

**Screen shows:**

```
  ================================================================
    ID  Status  Title                       Description
  ----------------------------------------------------------------
     1  [ ]     Prepare demo slides         Hackathon II present..
     2  [ ]     Write project README
     3  [ ]     Push code to GitHub
  ================================================================
  3 task(s)
```

**Narration:** *"View all tasks in a clean table. Status shows `[ ]` for pending."*

---

### [0:36 – 0:52] FEATURE 3 — UPDATE TASK

**Action:** Press `3` → Enter

```
  >> Update Task
  --------------------------------------------
  Task ID to update    : 1
  Current title        : Prepare demo slides
  New title            : Record demo video
  Current description  : Hackathon II presentation
  New description      :               ← (press Enter to keep)
  Task #1 updated successfully.
```

**Action:** Press `2` to view — confirm the change

```
  ================================================================
    ID  Status  Title                       Description
  ----------------------------------------------------------------
     1  [ ]     Record demo video           Hackathon II present..
     2  [ ]     Write project README
     3  [ ]     Push code to GitHub
  ================================================================
```

**Narration:** *"Update any field by ID. Press Enter to keep the existing value — no accidental overwrites."*

---

### [0:52 – 1:04] FEATURE 4 — TOGGLE COMPLETE

**Action:** Press `5` → Enter

```
  >> Toggle Task Status
  --------------------------------------------
  Task ID to toggle    : 2
  Task #2 marked as complete.
```

**Action:** Press `2` to view — show the `[x]` icon

```
  ================================================================
    ID  Status  Title                       Description
  ----------------------------------------------------------------
     1  [ ]     Record demo video           Hackathon II present..
     2  [x]     Write project README
     3  [ ]     Push code to GitHub
  ================================================================
```

**Narration:** *"Toggle any task between `[ ]` pending and `[x]` complete. One keystroke, instant feedback."*

---

### [1:04 – 1:20] FEATURE 5 — DELETE TASK

**Action:** Press `4` → Enter

```
  >> Delete Task
  --------------------------------------------
  Task ID to delete    : 3
  Delete 'Push code to GitHub'? (y/n) : y
  Task #3 deleted.
```

**Action:** Press `2` — final view

```
  ================================================================
    ID  Status  Title                       Description
  ----------------------------------------------------------------
     1  [ ]     Record demo video           Hackathon II present..
     2  [x]     Write project README
  ================================================================
  2 task(s)
```

**Narration:** *"Delete with a confirmation prompt — no accidental removals. The table updates instantly."*

---

### [1:20 – 1:30] CLOSE

**Action:** Press `0` → Enter

```
  Goodbye!
```

**Narration:** *"Phase I complete — in-memory, zero dependencies, 107 tests passing. Built spec-first, AI-generated, production-quality structure. Next: Phase II — REST API, database, and authentication."*

---

## Full Input Sequence (for one-shot run)

Copy-paste into the terminal to reproduce the entire demo in one session:

```
1
Prepare demo slides
Hackathon II presentation
1
Write project README

1
Push code to GitHub

2
3
1
Record demo video

2
5
2
2
4
3
y
2
0
```

---

## Timing Reference

| Timestamp | Feature | Duration |
|-----------|---------|----------|
| 0:00 – 0:06 | Launch | 6s |
| 0:06 – 0:24 | Add Task (×3) | 18s |
| 0:24 – 0:36 | View Tasks | 12s |
| 0:36 – 0:52 | Update Task | 16s |
| 0:52 – 1:04 | Toggle Complete | 12s |
| 1:04 – 1:20 | Delete Task | 16s |
| 1:20 – 1:30 | Close + outro | 10s |
| **Total** | | **~90s** |

---

## Recording Tips

- Set terminal to **80 columns × 30 rows** for consistent framing
- Type at **medium pace** — not too fast, not too slow; let each confirmation message settle for ~1s before the next keystroke
- Pause **2 seconds** on the task table after each view to let it register on screen
- Use **OBS** or **ShareX** (Windows) for recording; crop to the terminal window only
- Add **narration as voiceover** in post if recording silently during the session
