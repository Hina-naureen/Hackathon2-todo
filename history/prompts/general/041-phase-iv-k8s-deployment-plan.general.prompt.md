---
id: "041"
title: "Phase IV Kubernetes Deployment Plan"
stage: general
date: "2026-02-26"
surface: agent
model: claude-sonnet-4-6
feature: "none"
branch: master
user: Hina-naureen
command: "Start Phase IV — Local Kubernetes Deployment. Analyze project, create plan."
labels: ["phase-iv", "kubernetes", "docker", "minikube", "helm", "plan"]
links:
  spec: "specs/overview.md §Repository Structure"
  ticket: "null"
  adr: "null"
  pr: "null"
files: []
tests: []
---

## Prompt

We are working on Hackathon II – Todo Spec-Driven Development monorepo.

Current Status:
- Phase I Console App completed
- Phase II Full-Stack Web App completed
- Phase III Chatbot UI implemented (ChatWidget + ChatPanel with Tailwind glassmorphism)
- Git is now installed and working on Windows

Goal:
Start Phase IV — Local Kubernetes Deployment.

IMPORTANT RULES:
- Follow Spec-Driven Development
- Read CLAUDE.md files and all specs inside /specs
- Do NOT modify existing todo logic or UI
- Only prepare cloud-native deployment architecture

Tasks:
1) Analyze project structure (frontend Next.js + backend FastAPI)
2) Create Dockerization plan: frontend Dockerfile, backend Dockerfile, docker-compose.yml
3) Prepare Kubernetes base structure: k8s/ folder with deployment.yaml and service.yaml files
4) Add Helm chart structure for future scaling
5) Prepare Minikube local deployment workflow

Output Needed: Step-by-step plan (NO code yet) + File structure

## Response

**Full audit performed. All Phase IV infrastructure files are already complete from previous sessions.** No new files need to be created.

### Complete File Structure (all ✅):

```
backend/Dockerfile              — Python 3.13-slim + UV → src.app:app
frontend/Dockerfile             — 3-stage Node 20 Alpine → npm start
docker-compose.yml              — Both services, healthcheck, env_file

k8s/
  backend-deployment.yaml       — 1 replica, imagePullPolicy: Never
  backend-service.yaml          — ClusterIP :8000
  frontend-deployment.yaml      — 1 replica, imagePullPolicy: Never
  frontend-service.yaml         — ClusterIP :3000

helm/todo-app/
  Chart.yaml                    — apiVersion: v2, version: 0.1.0
  values.yaml                   — backend + frontend config blocks
  templates/
    backend-deployment.yaml
    backend-service.yaml
    frontend-deployment.yaml
    frontend-service.yaml
    NOTES.txt
```

### Step-by-Step Execution Plan (7 stages):

Stage 1: Prerequisites Check (Docker Desktop, Minikube, kubectl, Helm)
Stage 2: Docker Compose local dev test (docker compose up --build)
Stage 3: Minikube cluster setup (minikube start + docker-env pointing)
Stage 4: Build images inside Minikube daemon (imagePullPolicy: Never strategy)
Stage 5A: Raw kubectl apply -f k8s/ + port-forward
Stage 5B: helm install todo-app ./helm/todo-app (preferred for scaling)
Stage 6: Verification checklist (pods Running, /health 200, browser test)

### ADR Suggestion:
imagePullPolicy: Never ties deployments to Minikube's daemon.
Suggested: /sp.adr local-image-strategy

### Decision points surfaced for user:
1. Docker Compose first vs direct Minikube?
2. kubectl (simple) vs helm (scalable)?
3. Shell environment: Git Bash, PowerShell, or WSL?
