---
id: "042"
title: "Phase IV Execution Workflow Git Bash"
stage: general
date: "2026-02-26"
surface: agent
model: claude-sonnet-4-6
feature: "none"
branch: master
user: Hina-naureen
command: "Phase IV execution decisions: Docker Compose first, kubectl, Git Bash"
labels: ["phase-iv", "kubernetes", "docker-compose", "minikube", "kubectl", "git-bash"]
links:
  spec: "specs/overview.md §Repository Structure"
  ticket: "null"
  adr: "null"
  pr: "null"
files: []
tests: []
---

## Prompt

Docker Compose first for local testing.
Use Minikube with kubectl (not Helm yet).
Shell: Git Bash.

## Response

Full 6-stage execution workflow provided with concrete Git Bash commands.

### Pre-flight: all checks passed
- backend/.env ✅ DATABASE_URL + BETTER_AUTH_SECRET + ALLOWED_ORIGINS
- frontend/.env.local ✅ BETTER_AUTH_SECRET + NEXT_PUBLIC_API_URL
- backend/src/app.py ✅ /health endpoint at GET /health
- backend/agents/ ✅ exists (Dockerfile COPY agents/)
- backend/uv.lock ✅ exists (--frozen flag)
- frontend/package-lock.json ✅ exists (npm ci)

### Key execution notes:
- `eval $(minikube docker-env --shell bash)` — Git Bash specific flag, must run per session
- imagePullPolicy: Never — images must be built INSIDE minikube daemon, not host Docker
- Two port-forward terminals needed (backend :8000 and frontend :3000)
- Build arg NEXT_PUBLIC_API_URL is baked into frontend image at build time

### Stage summary:
1. docker compose up --build (smoke test both images)
2. minikube start + eval $(minikube docker-env --shell bash)
3. docker build -t todo-backend:latest ./backend
4. docker build --build-arg NEXT_PUBLIC_API_URL=http://localhost:8000 -t todo-frontend:latest ./frontend
5. kubectl apply -f k8s/ + kubectl get pods -w
6. kubectl port-forward svc/backend-service 8000:8000
   kubectl port-forward svc/frontend-service 3000:3000
7. kubectl delete -f k8s/ && minikube stop (teardown)
