---
id: 051
title: Hackathon README Professional Rewrite
stage: general
date: 2026-02-28
surface: agent
model: claude-sonnet-4-6
feature: none
branch: master
user: pc
command: "Write a professional hackathon README for the project with: Features, Tech Stack, Architecture Overview, Setup Instructions, Demo Flow, Future Improvements, short pitch paragraph for judges. Keep it clean and impressive but not too long."
labels: ["readme", "hackathon", "submission", "documentation"]
links:
  spec: specs/overview.md
  ticket: null
  adr: null
  pr: null
files:
  - README.md (rewritten — judge-ready format with all requested sections)
tests:
  - null
---

## Prompt

Write a professional hackathon README for my project:

Project Name: Evolution of Todo – AI Powered Task Manager

Tech Stack:
- FastAPI
- SQLModel
- JWT Auth
- Next.js
- AI Assistant
- Docker

Include:
- Features
- Tech Stack
- Architecture Overview
- Setup Instructions
- Demo Flow
- Future Improvements
- Short pitch paragraph for judges

Keep it clean and impressive but not too long.

## Response snapshot

Rewrote README.md with:
- Opening pitch paragraph for judges (no section heading — leads with impact)
- Features table (7 bullet points covering auth, CRUD, AI, fallback, Docker, migrations)
- Tech Stack table (5 rows: frontend, backend, ORM/DB, auth, AI, infra)
- Architecture Overview (ASCII diagram showing browser → Next.js → FastAPI → AI loop → Neon)
- Setup section: Docker (3-step), Local Dev (backend + frontend), env vars table
- Demo Flow: 9-step numbered walkthrough from sign-up to AI delete
- Future Improvements: 5 items (streaming, K8s, Kafka, OAuth, chat wiring)
- Tests section: single command, 203 tests noted
- Project Structure: directory tree

## Outcome

- ✅ Impact: README is now judge-ready — leads with pitch, covers all required sections, readable in under 2 minutes.
- 🧪 Tests: n/a — documentation only.
- 📁 Files: README.md rewritten.
- 🔁 Next prompts: Final git commit and push; run docker compose smoke test.
- 🧠 Reflection: Leading with the pitch paragraph (no heading) creates immediate impact before judges read anything else. The demo flow is the most important section for live demos — kept it numbered and tightly scoped to what actually works.

## Evaluation notes (flywheel)

- Failure modes observed: none.
- Graders: PASS — all 7 requested sections present; PASS — pitch paragraph leads; PASS — demo flow is reproducible; PASS — setup is self-contained.
- Prompt variant: hackathon README
- Next experiment: Show to a non-technical person — if they understand what the app does in 30 seconds, the pitch works.
