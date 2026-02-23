# Evolution of Todo - Constitution

## Core Principles

### I. Spec-Driven Development (NON-NEGOTIABLE)
No code is written without a corresponding spec. Every feature must follow the lifecycle: Specify → Plan → Tasks → Implement. Claude Code generates all code; manual coding is FORBIDDEN. Specs are the single source of truth.

### II. Technology Stack (LOCKED)
- Phase I: Python 3.13+, UV package manager
- Phase II: Next.js (App Router), FastAPI, SQLModel, Neon DB, Better Auth
- Phase III: OpenAI Agents SDK, Official MCP SDK, OpenAI ChatKit
- Phase IV: Docker, Minikube, Helm, kubectl-ai, Kagent
- Phase V: Kafka, Dapr, DigitalOcean Kubernetes (DOKS)
Stack changes require ADR + explicit user approval.

### III. Code Quality Standards
Clean code principles enforced. Functions have single responsibility. No hardcoded secrets — use .env files. Proper error handling at all system boundaries. Type hints required in all Python functions.

### IV. Project Structure Standards
```
project/
├── .specify/memory/     # Constitution and agent memory
├── specs/               # All feature specifications
├── src/                 # Source code
├── history/prompts/     # Prompt History Records (PHR)
├── history/adr/         # Architecture Decision Records
├── CLAUDE.md            # Claude Code instructions
└── README.md            # Setup documentation
```

### V. Feature Progression
- Phase I Basic: Add, Delete, Update, View, Mark Complete
- Phase II Basic: REST API + auth + Neon DB
- Phase III: AI chatbot + MCP server
- Phase IV: Kubernetes deployment
- Phase V: Advanced features + Kafka + Dapr + Cloud K8s

### VI. Simplicity First
Start simple. No over-engineering. YAGNI (You Aren't Gonna Need It). Each phase builds on the previous — do not implement future-phase features early.

## Security Requirements
- No secrets in source code
- All credentials via environment variables
- Input validation at all entry points
- SQL injection prevention (Phase II+)

## Development Workflow
1. Write spec for the feature
2. Generate plan from spec
3. Break plan into tasks
4. Implement via Claude Code
5. Record PHR after each major prompt
6. Suggest ADR for significant architectural decisions

## Governance
Constitution supersedes all other practices. Amendments require documentation and approval. All implementations must comply with the active phase's spec. Claude Code must re-read constitution at session start.

**Version**: 1.0.0 | **Ratified**: 2026-02-24 | **Last Amended**: 2026-02-24
