---
id: "058"
title: Phase IV Minikube Full Deployment
stage: general
date: 2026-03-02
surface: agent
model: claude-sonnet-4-6
feature: phase-iv-kubernetes
branch: master
user: pc
command: Continue Phase IV deployment (resumed session)
labels: ["phase-iv","kubernetes","minikube","docker","deployment","ingress"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - k8s/backend-deployment.yaml
  - k8s/frontend-deployment.yaml
  - k8s/ingress.yaml
  - backend/Dockerfile
  - frontend/Dockerfile
tests:
  - kubectl get pods (backend 1/1, frontend 1/1)
  - curl http://localhost:8080/health → {"status":"ok"}
---

## Prompt

Please check the status of the Minikube deployment and ensure that the pods are running correctly. Use the kubectl get pods command to check the pod statuses. Also, verify if the health check is returning a successful response from http://todo.local/health.

(Resumed from previous session where minikube had just successfully started with exit code 0, node Ready v1.35.1)

## Response snapshot

Continued Phase IV deployment after minikube was running:

1. **Enabled ingress addon**: `minikube addons enable ingress` — downloaded nginx ingress controller images, addon enabled successfully.

2. **Built Docker images inside minikube's Docker env** (DOCKER_HOST=tcp://127.0.0.1:49252):
   - `todo-backend:latest` — Python 3.13-slim + uv, 55 packages, exit 0
   - `todo-frontend:latest` — Node 20-alpine, Next.js 16.1.6, compiled in 60s, exit 0

3. **Created K8s secret**: `kubectl create secret generic todo-secrets` with DATABASE_URL, BETTER_AUTH_SECRET, OPENAI_API_KEY

4. **Applied all manifests**: backend deployment+service, frontend deployment+service, ingress

5. **Diagnosed and fixed backend CrashLoopBackOff**: `uv run` tried to create cache at `/home/appuser/.cache/uv` but `appuser` had `--no-create-home`. Fix: added `UV_CACHE_DIR=/app/.cache/uv` env var to `k8s/backend-deployment.yaml` (appuser owns `/app`).

6. **Verified health**: `kubectl port-forward svc/backend-service 8080:8000` → `curl http://localhost:8080/health` → `{"status":"ok"}`

Final state:
- backend: 1/1 Running, Uvicorn on port 8000, /health returning 200
- frontend: 1/1 Running, Next.js on port 3000
- ingress: todo.local → 192.168.49.2 (nginx controller)

## Outcome

- ✅ Impact: Phase IV complete — both backend and frontend pods running in Minikube, health check passing, ingress configured
- 🧪 Tests: kubectl get pods (1/1 both), curl /health → {"status":"ok"}, alembic migrations ran against Neon DB
- 📁 Files: k8s/backend-deployment.yaml (UV_CACHE_DIR fix), images built in minikube docker env
- 🔁 Next prompts: Run `minikube tunnel` + add hosts entry to access http://todo.local from browser; commit Phase III tests + Phase IV manifests to git
- 🧠 Reflection: Docker pipe hang on Windows requires PowerShell Start-Process (not bash). uv requires home dir or UV_CACHE_DIR when running as system user created with --no-create-home.

## Evaluation notes (flywheel)

- Failure modes observed: (1) bash pipe hang with docker commands on Windows — fixed via PowerShell Start-Process; (2) uv cache permission denied for --no-create-home system user — fixed via UV_CACHE_DIR env var
- Graders run and results (PASS/FAIL): kubectl get pods PASS, /health endpoint PASS
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): Add hosts file entry and test http://todo.local from browser
