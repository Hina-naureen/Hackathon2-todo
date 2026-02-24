---
id: 018
title: Phase II Demo Video Script 90 Seconds
stage: general
date: 2026-02-24
surface: agent
model: claude-sonnet-4-6
feature: phase-ii
branch: master
user: pc
command: "Generate Phase II demo video script under 90 seconds."
labels: ["demo","script","video","phase-ii","auth","persistence"]
links:
  spec: specs/overview.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/phase2-demo-script.md (created)
tests:
  - n/a — script document
---

## Prompt

Generate Phase II demo video script under 90 seconds.

## Response snapshot

Created `specs/phase2-demo-script.md` — a complete 88-second browser screen
recording script with voiceover, structured as 9 scenes.

Story: Alice signs up → creates 3 tasks → toggles one complete → edits another
→ deletes one → signs out → signs back in → verifies persistence.

Script covers every Phase II differentiator vs Phase I: auth, persistence, real-time UI updates, optimistic toggle, confirm dialog.

Includes timing reference table, 120-word voiceover read-through (~48 s speech
+ 42 s natural silence), one-shot action checklist, and recording tips.

## Outcome

- ✅ Impact: Ready-to-record 90-second demo script for Phase II.
- 📁 Files: 1 created.
- 🔁 Next: Record demo using the script, validate timing holds within 90 s.
- 🧠 Reflection: Built on Phase I script format (PHR 009) adapted for browser UX.

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): n/a
- Prompt variant: n/a
- Next experiment: do a dry run through the one-shot sequence and time it
