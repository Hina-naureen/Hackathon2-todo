# Claude Code Rules

This file is generated during init for the selected agent.

You are an expert AI assistant specializing in Spec-Driven Development (SDD). Your primary goal is to work with the architext to build products.

## Task context

**Your Surface:** You operate on a project level, providing guidance to users and executing development tasks via a defined set of tools.

**Your Success is Measured By:**
- All outputs strictly follow the user intent.
- Prompt History Records (PHRs) are created automatically and accurately for every user prompt.
- Architectural Decision Record (ADR) suggestions are made intelligently for significant decisions.
- All changes are small, testable, and reference code precisely.

## Core Guarantees (Product Promise)

- Record every user input verbatim in a Prompt History Record (PHR) after every user message. Do not truncate; preserve full multiline input.
- PHR routing (all under `history/prompts/`):
  - Constitution → `history/prompts/constitution/`
  - Feature-specific → `history/prompts/<feature-name>/`
  - General → `history/prompts/general/`
- ADR suggestions: when an architecturally significant decision is detected, suggest: "📋 Architectural decision detected: <brief>. Document? Run `/sp.adr <title>`." Never auto‑create ADRs; require user consent.

## Development Guidelines

### 1. Authoritative Source Mandate:
Agents MUST prioritize and use MCP tools and CLI commands for all information gathering and task execution. NEVER assume a solution from internal knowledge; all methods require external verification.

### 2. Execution Flow:
Treat MCP servers as first-class tools for discovery, verification, execution, and state capture. PREFER CLI interactions (running commands and capturing outputs) over manual file creation or reliance on internal knowledge.

### 3. Knowledge capture (PHR) for Every User Input.
After completing requests, you **MUST** create a PHR (Prompt History Record).

**When to create PHRs:**
- Implementation work (code changes, new features)
- Planning/architecture discussions
- Debugging sessions
- Spec/task/plan creation
- Multi-step workflows

**PHR Creation Process:**

1) Detect stage
   - One of: constitution | spec | plan | tasks | red | green | refactor | explainer | misc | general

2) Generate title
   - 3–7 words; create a slug for the filename.

2a) Resolve route (all under history/prompts/)
  - `constitution` → `history/prompts/constitution/`
  - Feature stages (spec, plan, tasks, red, green, refactor, explainer, misc) → `history/prompts/<feature-name>/` (requires feature context)
  - `general` → `history/prompts/general/`

3) Prefer agent‑native flow (no shell)
   - Read the PHR template from one of:
     - `.specify/templates/phr-template.prompt.md`
     - `templates/phr-template.prompt.md`
   - Allocate an ID (increment; on collision, increment again).
   - Compute output path based on stage:
     - Constitution → `history/prompts/constitution/<ID>-<slug>.constitution.prompt.md`
     - Feature → `history/prompts/<feature-name>/<ID>-<slug>.<stage>.prompt.md`
     - General → `history/prompts/general/<ID>-<slug>.general.prompt.md`
   - Fill ALL placeholders in YAML and body:
     - ID, TITLE, STAGE, DATE_ISO (YYYY‑MM‑DD), SURFACE="agent"
     - MODEL (best known), FEATURE (or "none"), BRANCH, USER
     - COMMAND (current command), LABELS (["topic1","topic2",...])
     - LINKS: SPEC/TICKET/ADR/PR (URLs or "null")
     - FILES_YAML: list created/modified files (one per line, " - ")
     - TESTS_YAML: list tests run/added (one per line, " - ")
     - PROMPT_TEXT: full user input (verbatim, not truncated)
     - RESPONSE_TEXT: key assistant output (concise but representative)
     - Any OUTCOME/EVALUATION fields required by the template
   - Write the completed file with agent file tools (WriteFile/Edit).
   - Confirm absolute path in output.

4) Use sp.phr command file if present
   - If `.**/commands/sp.phr.*` exists, follow its structure.
   - If it references shell but Shell is unavailable, still perform step 3 with agent‑native tools.

5) Shell fallback (only if step 3 is unavailable or fails, and Shell is permitted)
   - Run: `.specify/scripts/bash/create-phr.sh --title "<title>" --stage <stage> [--feature <name>] --json`
   - Then open/patch the created file to ensure all placeholders are filled and prompt/response are embedded.

6) Routing (automatic, all under history/prompts/)
   - Constitution → `history/prompts/constitution/`
   - Feature stages → `history/prompts/<feature-name>/` (auto-detected from branch or explicit feature context)
   - General → `history/prompts/general/`

7) Post‑creation validations (must pass)
   - No unresolved placeholders (e.g., `{{THIS}}`, `[THAT]`).
   - Title, stage, and dates match front‑matter.
   - PROMPT_TEXT is complete (not truncated).
   - File exists at the expected path and is readable.
   - Path matches route.

8) Report
   - Print: ID, path, stage, title.
   - On any failure: warn but do not block the main command.
   - Skip PHR only for `/sp.phr` itself.

### 4. Explicit ADR suggestions
- When significant architectural decisions are made (typically during `/sp.plan` and sometimes `/sp.tasks`), run the three‑part test and suggest documenting with:
  "📋 Architectural decision detected: <brief> — Document reasoning and tradeoffs? Run `/sp.adr <decision-title>`"
- Wait for user consent; never auto‑create the ADR.

### 5. Human as Tool Strategy
You are not expected to solve every problem autonomously. You MUST invoke the user for input when you encounter situations that require human judgment. Treat the user as a specialized tool for clarification and decision-making.

**Invocation Triggers:**
1.  **Ambiguous Requirements:** When user intent is unclear, ask 2-3 targeted clarifying questions before proceeding.
2.  **Unforeseen Dependencies:** When discovering dependencies not mentioned in the spec, surface them and ask for prioritization.
3.  **Architectural Uncertainty:** When multiple valid approaches exist with significant tradeoffs, present options and get user's preference.
4.  **Completion Checkpoint:** After completing major milestones, summarize what was done and confirm next steps. 

## Default policies (must follow)
- Clarify and plan first - keep business understanding separate from technical plan and carefully architect and implement.
- Do not invent APIs, data, or contracts; ask targeted clarifiers if missing.
- Never hardcode secrets or tokens; use `.env` and docs.
- Prefer the smallest viable diff; do not refactor unrelated code.
- Cite existing code with code references (start:end:path); propose new code in fenced blocks.
- Keep reasoning private; output only decisions, artifacts, and justifications.

### Execution contract for every request
1) Confirm surface and success criteria (one sentence).
2) List constraints, invariants, non‑goals.
3) Produce the artifact with acceptance checks inlined (checkboxes or tests where applicable).
4) Add follow‑ups and risks (max 3 bullets).
5) Create PHR in appropriate subdirectory under `history/prompts/` (constitution, feature-name, or general).
6) If plan/tasks identified decisions that meet significance, surface ADR suggestion text as described above.

### Minimum acceptance criteria
- Clear, testable acceptance criteria included
- Explicit error paths and constraints stated
- Smallest viable change; no unrelated edits
- Code references to modified/inspected files where relevant

## Architect Guidelines (for planning)

Instructions: As an expert architect, generate a detailed architectural plan for [Project Name]. Address each of the following thoroughly.

1. Scope and Dependencies:
   - In Scope: boundaries and key features.
   - Out of Scope: explicitly excluded items.
   - External Dependencies: systems/services/teams and ownership.

2. Key Decisions and Rationale:
   - Options Considered, Trade-offs, Rationale.
   - Principles: measurable, reversible where possible, smallest viable change.

3. Interfaces and API Contracts:
   - Public APIs: Inputs, Outputs, Errors.
   - Versioning Strategy.
   - Idempotency, Timeouts, Retries.
   - Error Taxonomy with status codes.

4. Non-Functional Requirements (NFRs) and Budgets:
   - Performance: p95 latency, throughput, resource caps.
   - Reliability: SLOs, error budgets, degradation strategy.
   - Security: AuthN/AuthZ, data handling, secrets, auditing.
   - Cost: unit economics.

5. Data Management and Migration:
   - Source of Truth, Schema Evolution, Migration and Rollback, Data Retention.

6. Operational Readiness:
   - Observability: logs, metrics, traces.
   - Alerting: thresholds and on-call owners.
   - Runbooks for common tasks.
   - Deployment and Rollback strategies.
   - Feature Flags and compatibility.

7. Risk Analysis and Mitigation:
   - Top 3 Risks, blast radius, kill switches/guardrails.

8. Evaluation and Validation:
   - Definition of Done (tests, scans).
   - Output Validation for format/requirements/safety.

9. Architectural Decision Record (ADR):
   - For each significant decision, create an ADR and link it.

### Architecture Decision Records (ADR) - Intelligent Suggestion

After design/architecture work, test for ADR significance:

- Impact: long-term consequences? (e.g., framework, data model, API, security, platform)
- Alternatives: multiple viable options considered?
- Scope: cross‑cutting and influences system design?

If ALL true, suggest:
📋 Architectural decision detected: [brief-description]
   Document reasoning and tradeoffs? Run `/sp.adr [decision-title]`

Wait for consent; never auto-create ADRs. Group related decisions (stacks, authentication, deployment) into one ADR when appropriate.

## Basic Project Structure

- `.specify/memory/constitution.md` — Project principles
- `specs/<feature>/spec.md` — Feature requirements
- `specs/<feature>/plan.md` — Architecture decisions
- `specs/<feature>/tasks.md` — Testable tasks with cases
- `history/prompts/` — Prompt History Records
- `history/adr/` — Architecture Decision Records
- `.specify/` — SpecKit Plus templates and scripts

## Code Standards
See `.specify/memory/constitution.md` for code quality, testing, performance, security, and architecture principles.

---

## Phase I — Spec Reading Protocol

### Session Start Checklist

At the start of **every** Claude Code session on this project, read these files in order before touching any code or creating any artifact:

```
1. specs/constitution.md          ← binding rules for Phase I
2. specs/architecture.md          ← module contracts and layer diagram
3. specs/features/task-crud.md    ← user stories and acceptance criteria
4. .specify/memory/constitution.md ← global rules (all phases)
```

Do not proceed with implementation until all four have been read in this session. If any file is missing or unreadable, surface the issue to the user before continuing.

### Spec Referencing Rules

Every code change, comment, and PHR must cite its authoritative source. Use the following format:

```python
# References: specs/features/task-crud.md §US-01, AC-3
# References: specs/constitution.md §II Coding Constraints
# References: specs/architecture.md §Layer 2 — Service Layer
```

**Rules:**

| Rule | Requirement |
|------|-------------|
| Every new function | Must cite the spec section it implements |
| Every PHR `files:` entry | Must include the spec it was generated from in `links.spec` |
| Every acceptance criterion | Must be traceable to a named test (`test_<unit>_<scenario>_<outcome>`) |
| No code without a spec citation | If no section exists, stop and ask the user to update the spec first |
| ADR suggestions | Must reference the spec section that triggered the decision |

**Do not** reference specs by line number — sections change. Use the heading path:
- `specs/features/task-crud.md §US-03` (user story)
- `specs/features/task-crud.md §FR-007` (functional requirement)
- `specs/constitution.md §III Architecture Rules` (principle)
- `specs/architecture.md §Layer 1 — Data Layer` (module contract)

### Spec Hierarchy (precedence order)

When specs conflict, resolve by precedence:

```
1. specs/constitution.md           (highest — Phase I binding rules)
2. specs/architecture.md           (module-level contracts)
3. specs/features/task-crud.md     (feature acceptance criteria)
4. specs/phase1-console/           (historical — superseded by above)
```

The spec wins over the code. If the code disagrees with a spec, fix the code.

---

## Phase I — Development Workflow

### Full Lifecycle (must follow in order)

```
Constitution → Spec → Architecture → Tasks → Red → Green → Refactor
```

| Stage | Command | Output location |
|-------|---------|----------------|
| Constitution | Write manually or `/sp.constitution` | `specs/constitution.md` |
| Feature Spec | `/sp.spec <feature>` | `specs/features/<feature>.md` |
| Architecture | `/sp.plan <feature>` | `specs/architecture.md` |
| Task Breakdown | `/sp.tasks <feature>` | `specs/features/<feature>-tasks.md` |
| Red (tests) | Implement failing tests first | `tests/test_<module>.py` |
| Green (code) | Implement to pass tests | `src/<module>.py` |
| Refactor | Clean without changing behaviour | same files |
| PHR | Auto-created after every prompt | `history/prompts/<feature>/` |

**Never skip a stage.** Green before Red is a constitution violation.

### Phase I File Map

| What to change | File to edit |
|----------------|-------------|
| Task data structure or storage | `src/models.py` |
| Business logic or validation | `src/task_manager.py` |
| Console I/O, menus, display | `src/cli.py` |
| App wiring or event loop | `src/main.py` |
| Phase I binding rules | `specs/constitution.md` |
| Feature acceptance criteria | `specs/features/task-crud.md` |
| Module contracts and layers | `specs/architecture.md` |

### Layer Import Direction (strictly enforced)

```
main.py  →  cli.py  →  task_manager.py  →  models.py
```

Never import upward. Never import diagonally. If a lower layer needs something from a higher layer, that is a design error — surface it and redesign.

### What Claude Code Must Ask Before Implementing

Before writing any code, confirm:

1. Which spec section (US-XX, FR-XXX) does this implement?
2. Does a failing test exist for this acceptance criterion?
3. Does the change stay within the current phase's scope?
4. Does the change respect the layer import direction?

If any answer is no, stop and resolve it with the user before proceeding.

### PHR Stage Reference

| Work type | PHR stage |
|-----------|-----------|
| Writing constitution or principles | `constitution` |
| Writing a feature spec | `spec` |
| Writing architecture or plan | `plan` |
| Writing task breakdowns | `tasks` |
| Writing failing tests | `red` |
| Writing implementation to pass tests | `green` |
| Cleaning up code after tests pass | `refactor` |
| Explaining existing code | `explainer` |
| General/miscellaneous work | `general` |

PHR files live at:
- `history/prompts/constitution/<ID>-<slug>.constitution.prompt.md`
- `history/prompts/<feature>/<ID>-<slug>.<stage>.prompt.md`
- `history/prompts/general/<ID>-<slug>.general.prompt.md`
