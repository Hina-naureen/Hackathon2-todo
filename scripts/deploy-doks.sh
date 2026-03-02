#!/usr/bin/env bash
# scripts/deploy-doks.sh — Phase V: Deploy Todo app to DigitalOcean Kubernetes (DOKS)
# References: specs/phase5-dapr-kafka.md §DOKS Deployment Architecture
#
# Usage:
#   export DATABASE_URL="postgresql+psycopg2://..."
#   export BETTER_AUTH_SECRET="$(openssl rand -hex 32)"
#   export OPENAI_API_KEY="sk-..."          # optional
#   export DOCR_REGISTRY="your-registry"    # DigitalOcean Container Registry name
#   export DOMAIN="todo.example.com"        # your domain
#   export IMAGE_TAG="v1.0.0"              # or "latest"
#   bash scripts/deploy-doks.sh
#
# Prerequisites:
#   - doctl (DigitalOcean CLI) installed and authenticated
#   - kubectl configured for your DOKS cluster
#   - helm 3.x installed
#   - docker installed
#
# What this script does:
#   1. Authenticate Docker with DigitalOcean Container Registry (DOCR)
#   2. Build + push backend and frontend images to DOCR
#   3. Install Dapr operator in the cluster (idempotent)
#   4. Apply Kafka dev cluster manifests
#   5. Apply Dapr component (Kafka pub/sub)
#   6. Install / upgrade the Helm chart with DOKS values
#   7. Wait for pods to be ready
#   8. Print access instructions

set -euo pipefail

# ── Colours ───────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# ── Required environment variables ────────────────────────────────────────────
: "${DATABASE_URL:?DATABASE_URL is required}"
: "${BETTER_AUTH_SECRET:?BETTER_AUTH_SECRET is required}"
: "${DOCR_REGISTRY:?DOCR_REGISTRY is required (DigitalOcean Container Registry name)}"
: "${DOMAIN:?DOMAIN is required (e.g. todo.example.com)}"
: "${IMAGE_TAG:=latest}"
OPENAI_API_KEY="${OPENAI_API_KEY:-}"

DOCR_URL="registry.digitalocean.com/${DOCR_REGISTRY}"
BACKEND_IMAGE="${DOCR_URL}/todo-backend:${IMAGE_TAG}"
FRONTEND_IMAGE="${DOCR_URL}/todo-frontend:${IMAGE_TAG}"

# ── Step 1: Authenticate Docker with DOCR ─────────────────────────────────────
info "Authenticating Docker with DigitalOcean Container Registry..."
doctl registry login

# ── Step 2: Build + push images ───────────────────────────────────────────────
info "Building backend image: ${BACKEND_IMAGE}"
docker build -t "${BACKEND_IMAGE}" ./backend

info "Pushing backend image..."
docker push "${BACKEND_IMAGE}"

info "Building frontend image: ${FRONTEND_IMAGE}"
docker build \
  --build-arg NEXT_PUBLIC_API_URL="https://${DOMAIN}" \
  --build-arg NEXT_PUBLIC_APP_URL="https://${DOMAIN}" \
  -t "${FRONTEND_IMAGE}" \
  ./frontend

info "Pushing frontend image..."
docker push "${FRONTEND_IMAGE}"

# ── Step 3: Install Dapr operator (idempotent) ────────────────────────────────
info "Installing Dapr operator in dapr-system namespace..."
helm repo add dapr https://dapr.github.io/helm-charts 2>/dev/null || true
helm repo update dapr

if helm status dapr -n dapr-system &>/dev/null; then
  info "Dapr already installed — upgrading..."
  helm upgrade dapr dapr/dapr -n dapr-system --wait --timeout=300s
else
  helm install dapr dapr/dapr \
    --namespace dapr-system \
    --create-namespace \
    --wait \
    --timeout=300s
fi

# ── Step 4: Deploy Kafka (dev cluster) ────────────────────────────────────────
info "Deploying Kafka (KRaft, single node)..."
kubectl apply -f k8s/kafka.yaml

info "Waiting for Kafka to be ready..."
kubectl wait --for=condition=ready pod -l app=kafka --timeout=120s || \
  warn "Kafka pod not ready in time — continuing anyway (it may still be starting)"

# ── Step 5: Apply Dapr component ──────────────────────────────────────────────
info "Applying Dapr Kafka pub/sub component..."
kubectl apply -f dapr/components/kafka-pubsub.yaml

# ── Step 6: Install / upgrade Helm chart ──────────────────────────────────────
info "Deploying todo-app Helm chart to DOKS..."
helm upgrade --install todo-app ./helm/todo-app \
  -f helm/todo-app/values-doks.yaml \
  --set secrets.databaseUrl="${DATABASE_URL}" \
  --set secrets.betterAuthSecret="${BETTER_AUTH_SECRET}" \
  --set secrets.openaiApiKey="${OPENAI_API_KEY}" \
  --set backend.image.repository="${DOCR_URL}/todo-backend" \
  --set backend.image.tag="${IMAGE_TAG}" \
  --set frontend.image.repository="${DOCR_URL}/todo-frontend" \
  --set frontend.image.tag="${IMAGE_TAG}" \
  --set ingress.host="${DOMAIN}" \
  --set backend.env.allowedOrigins="https://${DOMAIN}" \
  --set frontend.env.nextPublicApiUrl="https://${DOMAIN}" \
  --wait \
  --timeout=300s

# ── Step 7: Wait for pods ─────────────────────────────────────────────────────
info "Waiting for backend pod (with Dapr sidecar) to be ready..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=todo-backend --timeout=180s

info "Waiting for frontend pod to be ready..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=todo-frontend --timeout=180s

# ── Step 8: Print access instructions ────────────────────────────────────────
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  DOKS DEPLOYMENT COMPLETE${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  Domain: https://${DOMAIN}"
echo ""
echo "  App endpoints:"
echo "    https://${DOMAIN}          ← Frontend (Next.js)"
echo "    https://${DOMAIN}/docs     ← Swagger API docs"
echo "    https://${DOMAIN}/health   ← Health check"
echo ""
echo "  Verify deployment:"
echo "    kubectl get pods                              # all pods"
echo "    kubectl get ingress                           # ingress + LB IP"
echo "    kubectl logs -l app.kubernetes.io/name=todo-backend -c backend -f"
echo "    kubectl logs -l app.kubernetes.io/name=todo-backend -c daprd -f"
echo ""
echo "  Dapr dashboard (port-forward):"
echo "    kubectl port-forward svc/dapr-dashboard 8080:8080 -n dapr-system"
echo "    open http://localhost:8080"
echo ""
echo "  Kafka topic verification:"
echo "    kubectl exec -it \$(kubectl get pod -l app=kafka -o name) -- \\"
echo "      /opt/kafka/bin/kafka-topics.sh --list --bootstrap-server localhost:9092"
echo ""
echo "  Upgrade after image rebuild:"
echo "    IMAGE_TAG=v1.0.1 bash scripts/deploy-doks.sh"
echo ""
echo "  Uninstall:"
echo "    helm uninstall todo-app"
echo "    kubectl delete -f k8s/kafka.yaml"
echo "    kubectl delete -f dapr/components/kafka-pubsub.yaml"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
