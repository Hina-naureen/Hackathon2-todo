---
id: "043"
title: "Phase IV Minikube kubectl Execution Commands"
stage: general
date: "2026-02-26"
surface: agent
model: claude-sonnet-4-6
feature: "none"
branch: master
user: Hina-naureen
command: "Phase IV execution next step — Minikube deployment commands"
labels: ["phase-iv", "minikube", "kubectl", "docker-driver", "wsl2", "git-bash"]
links:
  spec: "specs/overview.md §Repository Structure"
  ticket: "null"
  adr: "null"
  pr: "null"
files: []
tests: []
---

## Prompt

Phase IV execution next step.

Environment:
- Windows + WSL2 enabled
- Docker Compose already working
- Using Git Bash shell
- Repo: Hackathon2-todo

Now generate SAFE step-by-step Minikube deployment commands.

Requirements:
- Do NOT recreate files
- Only execution commands
- Use existing k8s/ manifests
- Start Minikube using Docker driver
- Apply manifests using kubectl
- Show verification steps (pods, services, URLs)

Give commands one-by-one with explanation.

## Response

13-step Minikube execution workflow provided. Key decisions:

- Used `minikube image load` instead of rebuilding inside Minikube daemon —
  safer since Docker Compose already built both images on host daemon.
- Driver: --driver=docker (uses Docker Desktop, no VirtualBox/Hyper-V needed)
- imagePullPolicy: Never in k8s manifests — requires images loaded via minikube image load
- Two separate port-forward terminals: svc/backend-service :8000 and svc/frontend-service :3000
- Teardown: kubectl delete -f k8s/ && minikube stop

Steps summary:
1.  minikube start --driver=docker
2.  minikube status
3.  kubectl cluster-info
4.  minikube image load todo-backend:latest
5.  minikube image load todo-frontend:latest
6.  minikube image ls | grep todo
7.  kubectl apply -f k8s/
8.  kubectl get pods -w
9.  kubectl get services
10. kubectl port-forward svc/backend-service 8000:8000
11. kubectl port-forward svc/frontend-service 3000:3000
12. curl http://localhost:8000/health
13. start http://localhost:3000
