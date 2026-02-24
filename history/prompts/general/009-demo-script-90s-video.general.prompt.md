---
id: "009"
title: Demo Script 90-Second Video
stage: general
date: 2026-02-24
surface: agent
model: claude-sonnet-4-6
feature: none
branch: master
user: pc
command: "Generate demo script for 90-second video showing all 5 features"
labels: ["demo","script","video","documentation","phase-1"]
links:
  spec: specs/features/task-crud.md
  ticket: null
  adr: null
  pr: null
files:
  - DEMO.md
tests:
  - "full input sequence verified against live app output"
---

## Prompt

Generate demo script for 90-second video showing:
- Add task
- View tasks
- Update task
- Toggle complete
- Delete task

## Response snapshot

Created DEMO.md with a complete 90-second walkthrough script.

Structure:
- Setup section: `cls` + `uv run todo`
- 7 timed scenes with exact keystrokes, screen output, and narration cues
- Coherent task story: "Prepare demo slides" → "Record demo video" (updated), "Write project README" (toggled complete), "Push code to GitHub" (deleted)
- Full one-shot input sequence for reproducing the entire demo in a single session
- Timing reference table (7 rows, total ~90s)
- Recording tips (terminal size, pacing, OBS/ShareX, voiceover note)

All terminal output verified against the live running app before writing the script.

## Outcome

- ✅ Impact: Production-ready demo script; coherent task story; exact keystrokes and screen output included
- 🧪 Tests: Live app output captured and verified before scripting
- 📁 Files: DEMO.md (created)
- 🔁 Next prompts: Phase II planning — FastAPI + SQLModel + Neon DB + Better Auth
- 🧠 Reflection: Used real app output captured by running the app to ensure every line in the script matches actual behaviour

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): live output verified PASS
- Prompt variant (if applicable): initial
- Next experiment: record the demo using the script and validate timing holds within 90s
