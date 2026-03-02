# frontend/Dockerfile
# References: specs/overview.md §Repository Structure
#             specs/ui/pages.md §Production Build
#
# Build:  docker build -t todo-frontend:latest .
# Run:    docker run -p 3000:3000 todo-frontend:latest
# Minikube: eval $(minikube docker-env) && docker build -t todo-frontend:latest .
#
# NOTE: NEXT_PUBLIC_API_URL is embedded at build time.
#       For browser access pass: --build-arg NEXT_PUBLIC_API_URL=http://localhost:8000

# ── Stage 1: Install dependencies ─────────────────────────────────────────────
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# ── Stage 2: Build ────────────────────────────────────────────────────────────
FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ARG NEXT_PUBLIC_APP_URL=http://localhost:3000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_APP_URL=$NEXT_PUBLIC_APP_URL

RUN npm run build

# ── Stage 3: Production runner ────────────────────────────────────────────────
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

# Use the built-in node user (uid 1000) — required for K8s runAsNonRoot: true.
RUN chown -R node:node /app
USER node

EXPOSE 3000

CMD ["npm", "start"]
