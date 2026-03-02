#!/usr/bin/env bash
# scripts/deploy-minikube.sh — Phase IV: Deploy Todo app to Minikube
# References: specs/architecture.md §Phase IV Layer Diagram
#
# Usage:
#   bash scripts/deploy-minikube.sh
#
# Prerequisites:
#   - minikube installed
#   - docker installed
#   - kubectl available
#   - backend/.env contains DATABASE_URL and BETTER_AUTH_SECRET
#
# What this script does:
#   1. Start Minikube (Docker driver)
#   2. Enable nginx Ingress addon
#   3. Point Docker CLI to Minikube's Docker daemon
#   4. Build backend + frontend images inside Minikube
#   5. Create Kubernetes Secret from backend/.env
#   6. Apply all k8s manifests
#   7. Wait for pods to be Ready
#   8. Print access instructions

set -euo pipefail

# ── Colours ───────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# ── Load env vars from backend/.env ──────────────────────────────────────────
ENV_FILE="backend/.env"
[[ -f "$ENV_FILE" ]] || error "backend/.env not found. Run from project root."

# Parse only key=value lines (skip comments and blank lines)
export $(grep -v '^\s*#' "$ENV_FILE" | grep -v '^\s*$' | xargs)

[[ -n "${DATABASE_URL:-}" ]]       || error "DATABASE_URL not set in $ENV_FILE"
[[ -n "${BETTER_AUTH_SECRET:-}" ]] || error "BETTER_AUTH_SECRET not set in $ENV_FILE"

OPENAI_API_KEY="${OPENAI_API_KEY:-}"

# ── Step 1: Start Minikube ────────────────────────────────────────────────────
info "Starting Minikube (driver=docker)..."
minikube start --driver=docker --memory=4096 --cpus=2 || true  # OK if already running
minikube status

# ── Step 2: Enable nginx Ingress addon ────────────────────────────────────────
info "Enabling nginx Ingress addon..."
minikube addons enable ingress

# ── Step 3: Point Docker to Minikube's daemon ─────────────────────────────────
info "Pointing Docker CLI to Minikube's Docker daemon..."
eval "$(minikube docker-env)"

# ── Step 4: Build Docker images ───────────────────────────────────────────────
info "Building backend image (todo-backend:latest)..."
docker build -t todo-backend:latest ./backend

info "Building frontend image (todo-frontend:latest) with todo.local API URL..."
docker build \
  --build-arg NEXT_PUBLIC_API_URL=http://todo.local \
  --build-arg NEXT_PUBLIC_APP_URL=http://todo.local \
  -t todo-frontend:latest \
  ./frontend

# ── Step 5: Create / update Kubernetes Secret ─────────────────────────────────
info "Creating Kubernetes Secret 'todo-secrets'..."
kubectl create secret generic todo-secrets \
  --from-literal=DATABASE_URL="$DATABASE_URL" \
  --from-literal=BETTER_AUTH_SECRET="$BETTER_AUTH_SECRET" \
  --from-literal=OPENAI_API_KEY="$OPENAI_API_KEY" \
  --dry-run=client -o yaml | kubectl apply -f -

# ── Step 6: Apply all k8s manifests ───────────────────────────────────────────
info "Applying k8s manifests..."
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/backend-service.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/frontend-service.yaml
kubectl apply -f k8s/ingress.yaml

# ── Step 7: Wait for pods ─────────────────────────────────────────────────────
info "Waiting for backend pod to be Ready (timeout 120s)..."
kubectl wait --for=condition=ready pod -l app=todo-backend --timeout=120s

info "Waiting for frontend pod to be Ready (timeout=120s)..."
kubectl wait --for=condition=ready pod -l app=todo-frontend --timeout=120s

# ── Step 8: Print access instructions ────────────────────────────────────────
MINIKUBE_IP=$(minikube ip)

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  DEPLOYMENT COMPLETE${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  Minikube IP: $MINIKUBE_IP"
echo ""
echo "  Add to your hosts file:"
echo -e "  ${YELLOW}$MINIKUBE_IP  todo.local${NC}"
echo ""
echo "  Linux/Mac:  echo '$MINIKUBE_IP  todo.local' | sudo tee -a /etc/hosts"
echo "  Windows:    Add '$MINIKUBE_IP  todo.local' to C:\\Windows\\System32\\drivers\\etc\\hosts"
echo ""
echo "  Then open:"
echo "    http://todo.local          ← App (Next.js)"
echo "    http://todo.local/docs     ← Swagger API"
echo "    http://todo.local/health   ← Health check"
echo ""
echo "  Useful commands:"
echo "    kubectl get pods -w                         # watch pod status"
echo "    kubectl get ingress todo-ingress            # check ingress IP"
echo "    kubectl logs -l app=todo-backend -f         # backend logs"
echo "    kubectl logs -l app=todo-frontend -f        # frontend logs"
echo "    kubectl describe secret todo-secrets        # verify secret (values redacted)"
echo ""
echo "  To stop:  minikube stop"
echo "  To clean: minikube delete"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
