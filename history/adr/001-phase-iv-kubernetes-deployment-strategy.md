# ADR-001: Phase IV Kubernetes Deployment Strategy

**Date:** 2026-03-02
**Status:** Accepted
**Deciders:** Hackathon II Team
**References:** specs/architecture.md §Phase IV Layer Diagram

---

## Context

Phase IV requires containerising the full-stack app (Next.js + FastAPI) and deploying it on a local Kubernetes cluster for demonstration. Three interconnected decisions had to be made:

1. Which local Kubernetes distribution to use
2. How to manage and inject secrets safely
3. How to run the Python backend inside a minimal Docker image without root access

---

## Decision 1 — Minikube + nginx Ingress (not Kind, k3s, or Docker Desktop Kubernetes)

### Options Considered

| Option | Pros | Cons |
|--------|------|------|
| **Minikube** | First-class addon system (`minikube addons enable ingress`), stable Windows Docker driver, excellent tooling | Heavier than Kind; requires separate minikube binary |
| Kind | Lightweight, fast cluster creation | No built-in ingress addon; manual nginx controller installation |
| k3s | Production-grade, very fast | Poor Windows support; requires WSL2 or Linux |
| Docker Desktop K8s | Zero installation | Single-node, no addon system, licence restrictions for enterprise |

### Decision

**Minikube with Docker driver** on Windows, with nginx Ingress enabled via `minikube addons enable ingress`.

### Rationale

- The `minikube addons enable ingress` command installs a pre-tested nginx controller version in one step — no manual YAML download or version pinning required.
- The Docker driver works reliably on Windows without Hyper-V or WSL2 prerequisites.
- Path-based Ingress routing (`/api → backend`, `/* → frontend`) on a single `todo.local` hostname mirrors real-world cluster topology.

### Consequences

- All team members must have Minikube installed; `scripts/deploy-minikube.sh` automates the full setup.
- Images are built inside Minikube's Docker daemon (`eval $(minikube docker-env)`) — no external registry required.
- A `/etc/hosts` (or `C:\Windows\System32\drivers\etc\hosts`) entry is required for `todo.local` resolution.

---

## Decision 2 — K8s Secret + Helm `required` guard (no secrets in git)

### Options Considered

| Option | Security | Usability |
|--------|----------|-----------|
| **K8s Secret + `required` guard** | Secrets never touch git; fail-fast on missing values | Operator must `--set` values at install time |
| Hardcode in values.yaml | Simple | Critical security failure — credentials in git history |
| External Secrets Operator (Vault, AWS SSM) | Best-in-class | Disproportionate complexity for a hackathon |
| `.env` file mounted as K8s volume | Acceptable | Requires manual secret management per cluster |

### Decision

**K8s Secret created from Helm `--set` flags at install time**, with `helm/todo-app/templates/secrets.yaml` using Helm's `required` function on mandatory keys.

```yaml
DATABASE_URL: {{ required "secrets.databaseUrl is required" .Values.secrets.databaseUrl | quote }}
```

### Rationale

- `values.yaml` contains zero default secret values (empty strings) and a comment block documenting this constraint.
- `required` causes `helm install` to abort with a clear error message if the operator forgets a mandatory key — no silent SQLite fallback or empty token.
- `stringData` (not `data:`) avoids double-encoding bugs; Kubernetes base64-encodes automatically.
- This pattern is directly portable to real clusters with CI/CD pipelines passing secrets via environment variables.

### Consequences

- The `helm install` command **must** include `--set secrets.databaseUrl=...` and `--set secrets.betterAuthSecret=...`.
- `helm/secrets.override.yaml` is gitignored as an alternative to `--set` flags.
- Helm `upgrade` also requires the same `--set` flags (secrets are not persisted across upgrades unless using `--reuse-values`).

---

## Decision 3 — `UV_CACHE_DIR` env var for non-root uv runtime

### Problem

The backend Dockerfile creates a system user with `--no-create-home`:

```dockerfile
RUN useradd --system --uid 1000 --no-create-home appuser
```

`uv` attempts to write its package cache to `~/.cache/uv`. Without a home directory, this resolves to `/root/.cache/uv` (owned by root), causing a `PermissionError` at container startup → CrashLoopBackOff.

### Decision

Set `UV_CACHE_DIR=/app/.cache/uv` as an environment variable in both `k8s/backend-deployment.yaml` and `helm/todo-app/templates/backend-deployment.yaml`.

```yaml
- name: UV_CACHE_DIR
  value: "/app/.cache/uv"
```

Since `chown -R appuser /app` runs in the Dockerfile build step, `appuser` owns `/app` and all subdirectories — including the cache directory that `uv` will create at runtime.

### Rationale

- Smallest possible fix: one env var, no Dockerfile change, no `initContainer`.
- `/app/.cache/uv` is writable by `appuser` without granting any additional privileges.
- Consistent across raw K8s manifests and Helm templates.

### Consequences

- Container startup time may be slightly longer if the cache is cold (uv re-downloads packages on first run after pod restart). This is acceptable for a local Minikube deployment.
- In production with persistent volumes, `UV_CACHE_DIR` should point to a PVC mount for faster restarts.

---

## Summary

| Decision | Choice | Key Benefit |
|----------|--------|-------------|
| Local K8s distribution | Minikube + Docker driver | One-command ingress setup on Windows |
| Secret management | K8s Secret + Helm `required` | Zero secrets in git; fail-fast validation |
| uv cache in Docker | `UV_CACHE_DIR=/app/.cache/uv` | Non-root container runs without CrashLoopBackOff |
