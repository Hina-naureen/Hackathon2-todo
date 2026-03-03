# backend/Dockerfile
# References: specs/overview.md §Repository Structure
#             specs/api/rest-endpoints.md §CORS Configuration
#
# Build:  docker build -t todo-backend:latest .
# Run:    docker run -p 8000:8000 --env-file .env todo-backend:latest
# Minikube: eval $(minikube docker-env) && docker build -t todo-backend:latest .

FROM python:3.13-slim

# Install UV (fast Python package manager)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency manifest + lock file first (layer-cache friendly)
COPY backend/pyproject.toml backend/uv.lock ./

# Install production dependencies only
RUN uv sync --frozen --no-dev

# Copy application source
COPY backend/ .

# Create non-root user (uid 1000) and fix ownership before switching user.
# Required for Kubernetes securityContext.runAsNonRoot: true.
RUN useradd --system --uid 1000 --no-create-home appuser \
    && mkdir -p /app/.cache/uv \
    && chown -R appuser /app

ENV UV_CACHE_DIR=/app/.cache/uv

USER appuser

EXPOSE 8000

# Run migrations then start the server
CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn src.app:app --host 0.0.0.0 --port 8000"]
