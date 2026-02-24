# Phase II — 90-Second Demo Script

**Version:** 1.0.0
**Date:** 2026-02-24
**Phase:** II
**Format:** Browser screen recording with voiceover
**Target length:** 88 seconds
**Story:** A new user signs up, manages a Hackathon task list, signs out, and signs back in to prove persistence.

---

## Pre-Recording Setup

```bash
# Terminal A — backend (leave running, hide window)
cd backend
uv run uvicorn src.app:app --reload --port 8000

# Terminal B — frontend (leave running, hide window)
cd frontend
npm run dev
```

**Browser:** Chrome or Firefox, 1280 × 800, zoom 100 %
**DevTools:** Closed
**Starting URL:** `http://localhost:3000` (will auto-redirect to `/sign-in`)
**Existing accounts:** None — fresh `.data/users.json` (delete it if it exists: `rm frontend/.data/users.json`)

---

## Scene Breakdown

---

### Scene 1 — Hook (0 s – 8 s)

**Screen state:** Browser at `http://localhost:3000`, sign-in page just loaded.

**Actions:**
- No clicks yet. Camera on sign-in page.

**Voiceover:**
> "Phase I was a Python console app. Phase II is a full-stack web app —
> Next.js frontend, FastAPI backend, PostgreSQL database, JWT auth.
> Same task logic. New everything else."

**On screen:** `/sign-in` page — `"Evolution of Todo"` heading, email + password fields.

---

### Scene 2 — Sign Up (8 s – 24 s)

**Screen state:** `/sign-in` page.

**Actions:**
1. Click `"Sign up →"` link (bottom of the card) → navigates to `/sign-up`
2. Click **Name** field → type `Alice`
3. Tab → type `alice@demo.com`
4. Tab → type `hackathon2`
5. Click `"Create Account"` → spinner for ~0.5 s → redirects to `/tasks`

**Voiceover:**
> "New user. Click sign up —"
> *(typing)* "— name, email, password."
> "Submit."
> "Session established. Redirected to the task list."

**On screen after redirect:**
```
Evolution of Todo          [alice@demo.com]  [Sign Out]
─────────────────────────────────────────────────────
My Tasks                                  [+ Add Task]

  No tasks yet. Add your first task.

  0 task(s)
```

---

### Scene 3 — Create Three Tasks (24 s – 46 s)

**Task 1 (24 s – 31 s)**

1. Click `"+ Add Task"` → modal opens
2. Type `Set up dev environment`
3. Tab → type `Python, Node, uv, npm`
4. Click `"Add Task"` → modal closes, task appears

**Task 2 (31 s – 38 s)**

1. Click `"+ Add Task"`
2. Type `Build API endpoints`
3. Tab → type `FastAPI + SQLModel`
4. Click `"Add Task"`

**Task 3 (38 s – 46 s)**

1. Click `"+ Add Task"`
2. Type `Record demo video`
3. Tab → leave description empty
4. Click `"Add Task"`

**Voiceover:**
> "Add three tasks —"
> *(brief pause for each)*
> "— no page reloads. List updates instantly."

**On screen after all three:**
```
  [ ]  Set up dev environment   Python, Node, uv, npm      [✎][×]
  [ ]  Build API endpoints      FastAPI + SQLModel          [✎][×]
  [ ]  Record demo video                                    [✎][×]

  3 task(s)
```

---

### Scene 4 — Toggle Complete (46 s – 53 s)

**Actions:**
1. Click the checkbox `[ ]` on `"Set up dev environment"`
   - Checkbox immediately flips to `[x]` (optimistic update)
   - Server confirms, checkbox stays

**Voiceover:**
> "Toggle done — optimistic update, no waiting."

**On screen:**
```
  [x]  ~~Set up dev environment~~   Python, Node, uv, npm  [✎][×]
  [ ]  Build API endpoints          FastAPI + SQLModel      [✎][×]
  [ ]  Record demo video                                    [✎][×]
```

---

### Scene 5 — Edit a Task (53 s – 63 s)

**Actions:**
1. Click `✎` on `"Build API endpoints"`
   - Modal opens, pre-filled: title `"Build API endpoints"`, description `"FastAPI + SQLModel"`
2. Click into description field → clear → type `FastAPI + SQLModel + Neon DB`
3. Click `"Save"` → modal closes, description updates inline

**Voiceover:**
> "Edit — pre-filled with current values."
> "Save. Updated in place."

**On screen after save:**
```
  [ ]  Build API endpoints   FastAPI + SQLModel + Neon DB   [✎][×]
```

---

### Scene 6 — Delete a Task (63 s – 72 s)

**Actions:**
1. Click `×` on `"Build API endpoints"` → confirmation dialog appears:
   ```
   Delete "Build API endpoints"?
   This cannot be undone.
   [Cancel]   [Delete]
   ```
2. Click `"Delete"` → dialog closes, task removed from list

**Voiceover:**
> "Delete — always confirms first."
> "Gone. Two tasks remain."

**On screen:**
```
  [x]  ~~Set up dev environment~~                          [✎][×]
  [ ]  Record demo video                                   [✎][×]

  2 task(s)
```

---

### Scene 7 — Sign Out (72 s – 77 s)

**Actions:**
1. Click `"Sign Out"` in the header
   - Redirected to `/sign-in`

**Voiceover:**
> "Sign out. Session cleared."

**On screen:** `/sign-in` page.

---

### Scene 8 — Sign In + Verify Persistence (77 s – 88 s)

**Actions:**
1. Type `alice@demo.com`
2. Tab → type `hackathon2`
3. Click `"Sign In"` → redirected to `/tasks`

**Voiceover:**
> "Sign back in —"
> "— both tasks are still here. Completed state preserved."
> "Phase I logic. Phase II persistence."

**On screen:**
```
Evolution of Todo          [alice@demo.com]  [Sign Out]
──────────────────────────────────────────────────────
My Tasks                                 [+ Add Task]

  [x]  ~~Set up dev environment~~                         [✎][×]
  [ ]  Record demo video                                  [✎][×]

  2 task(s)
```

---

### Scene 9 — Hold on final frame (88 s – 90 s)

Hold on the task list. No action.

---

## Timing Reference

| Scene | Start | End | Duration | Key action |
|-------|-------|-----|----------|------------|
| 1 — Hook | 0 s | 8 s | 8 s | Static — voiceover only |
| 2 — Sign Up | 8 s | 24 s | 16 s | `/sign-up` form → redirect |
| 3 — Create Tasks | 24 s | 46 s | 22 s | 3 × Add Task modal |
| 4 — Toggle | 46 s | 53 s | 7 s | Checkbox click |
| 5 — Edit | 53 s | 63 s | 10 s | Edit modal, save |
| 6 — Delete | 63 s | 72 s | 9 s | Confirm dialog, delete |
| 7 — Sign Out | 72 s | 77 s | 5 s | Header button |
| 8 — Sign In + Verify | 77 s | 88 s | 11 s | Sign in → task list |
| 9 — Hold | 88 s | 90 s | 2 s | Static |
| **Total** | | | **90 s** | |

---

## Voiceover Script (read-through)

Read at a calm, even pace — approximately 2.5 words per second.

```
[0s]  Phase I was a Python console app.
      Phase II is a full-stack web app —
      Next.js frontend, FastAPI backend, PostgreSQL database, JWT auth.
      Same task logic. New everything else.

[8s]  New user. Click sign up —
      — name, email, password. Submit.
      Session established. Redirected to the task list.

[24s] Add three tasks —
      — no page reloads. List updates instantly.

[46s] Toggle done — optimistic update, no waiting.

[53s] Edit — pre-filled with current values. Save. Updated in place.

[63s] Delete — always confirms first. Gone. Two tasks remain.

[72s] Sign out. Session cleared.

[77s] Sign back in —
      — both tasks are still here. Completed state preserved.
      Phase I logic. Phase II persistence.
```

**Total words:** ~120 · at 2.5 wps = **48 s of speech**, leaving ~42 s of natural silence during typing and clicks.

---

## One-Shot Action Sequence

Use this as a checklist while recording to stay on pace.

```
[ ] Navigate to http://localhost:3000
[ ] Click "Sign up →"
[ ] Type: Alice / alice@demo.com / hackathon2 → Create Account
[ ] + Add Task → "Set up dev environment" / "Python, Node, uv, npm" → Add
[ ] + Add Task → "Build API endpoints" / "FastAPI + SQLModel" → Add
[ ] + Add Task → "Record demo video" / (empty) → Add
[ ] Click checkbox on "Set up dev environment"
[ ] Click ✎ on "Build API endpoints" → change desc → Save
[ ] Click × on "Build API endpoints" → Delete
[ ] Click "Sign Out"
[ ] Type: alice@demo.com / hackathon2 → Sign In
[ ] Hold on task list — 2 tasks, 1 complete
[ ] Stop recording
```

---

## Recording Tips

| Setting | Value |
|---------|-------|
| Resolution | 1280 × 800 (or 1920 × 1080 downscaled) |
| Browser zoom | 100 % |
| Font size | Default (no zoom, no accessibility scaling) |
| Recording tool | OBS Studio, Loom, or ShareX |
| Cursor highlight | Enable — makes clicks visible |
| Mouse speed | Slow down to ~60 % normal speed |
| Tab autocomplete | Disabled — type everything manually |
| Network tab | Closed |
| Notifications | OS focus mode ON |
| Post-processing | Trim 0.5 s from start and end; no cuts needed if paced correctly |

**Audio tip:** Record voiceover as a separate track and layer it in post. This lets you re-record lines independently without re-doing the screen capture.

**If you run long:** The most compressible scenes are Scene 3 (drop to 2 tasks instead of 3) and Scene 5 (edit title instead of description — faster to clear and retype).

---

## References

| Document | Path |
|----------|------|
| Phase II overview | `specs/overview.md` |
| UI pages spec | `specs/ui/pages.md` |
| Auth spec | `specs/features/authentication.md` |
| Verification checklist | `specs/phase2-verification-checklist.md` |
| Phase I demo script | `DEMO.md` |
