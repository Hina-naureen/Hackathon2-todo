---
id: "001"
title: Phase I Constitution — Spec-Driven Console Todo App
stage: constitution
date: 2026-02-24
surface: agent
model: claude-sonnet-4-6
feature: none
branch: master
user: pc
command: "Create Phase I Constitution file for Spec-Driven Todo Console App"
labels: ["constitution","phase-1","spec-driven","architecture","python","console"]
links:
  spec: specs/phase1-console/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/constitution.md
tests:
  - null
---

## Prompt

Create a Phase I Constitution file for a Spec-Driven Todo Console App.

Requirements:
- Spec-Driven Development only (no manual coding)
- Python 3.13 console application
- In-Memory task storage
- Clean architecture and modular structure
- Features:
  - Add Task
  - Delete Task
  - Update Task
  - View Tasks
  - Mark Complete

Output:
Create a markdown file: /specs/constitution.md

Include:
- Project principles
- Coding constraints
- Architecture rules
- Naming conventions
- Testing philosophy
- Claude Code usage guidelines

## Response snapshot

Created `specs/constitution.md` with nine sections:
- I. Project Principles (SDD mandate, Claude Code role, YAGNI, smallest viable diff)
- II. Coding Constraints (Python 3.13+, UV, stdlib only, type hints, naming rules, forbidden patterns)
- III. Architecture Rules (three-layer model: CLI → Service → Model; strict import boundaries; in-memory store contract)
- IV. Naming Conventions (file names, class names, method signatures for TaskService, constants)
- V. Testing Philosophy (test-first mandate, three-layer test strategy, naming convention, coverage requirements, isolation rules)
- VI. Claude Code Usage Guidelines (session start protocol, prompt discipline, PHR mandate, ADR triggers, forbidden actions)
- VII. Error Handling Contract (ValueError from service, None/False returns, top-level catch)
- VIII. Out of Scope for Phase I (explicit exclusions)
- IX. Governance (amendment process, ADR mechanism, version control)

## Outcome

- ✅ Impact: Establishes binding rules for all Phase I development; prevents scope creep and architectural violations
- 🧪 Tests: No tests run (constitution is a document artifact)
- 📁 Files: specs/constitution.md (created)
- 🔁 Next prompts: Run `/sp.spec` to write a feature spec, or `/sp.plan` to generate an architecture plan
- 🧠 Reflection: Constitution is thorough and phase-scoped; separates concerns clearly; references existing spec and project structure

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): N/A — document artifact
- Prompt variant (if applicable): initial
- Next experiment: validate constitution against existing spec.md for consistency gaps
