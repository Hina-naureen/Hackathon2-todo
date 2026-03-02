# Phase V Specification — Event-Driven Architecture (Kafka + Dapr + DOKS)

**Version:** 1.0.0
**Date:** 2026-03-02
**Status:** Active
**Phase:** V
**Supersedes:** Phase IV (extends, does not replace)
**Constitution:** `.specify/memory/constitution.md`

---

## Goal

Extend the Phase IV Kubernetes deployment with an **event-driven backbone** using Apache Kafka as the message broker and **Dapr** as the sidecar abstraction layer. Deploy the complete stack to **DigitalOcean Kubernetes Service (DOKS)** for a production-grade cloud environment.

Every task mutation (create / update / delete / toggle) emits a domain event to Kafka via Dapr's pub/sub API. Events enable future consumers (audit logs, notifications, analytics, real-time sync) without coupling them to the task service.

---

## Phase V Stack

| Layer | Technology | Version |
|-------|------------|---------|
| **Message Broker** | Apache Kafka (KRaft mode) | 3.7+ |
| **Sidecar / Abstraction** | Dapr | 1.13+ |
| **Event Publisher** | Dapr HTTP pub/sub API | v1.0 |
| **Cloud K8s** | DigitalOcean Kubernetes Service (DOKS) | 1.30+ |
| **Container Registry** | DigitalOcean Container Registry (DOCR) | — |
| **Backend** | FastAPI (unchanged from Phase III) | — |
| **Async HTTP Client** | httpx | 0.27+ |

Stack locked by constitution — changes require ADR + user approval.

---

## Scope

### In Scope

| # | Feature | Deliverable |
|---|---------|-------------|
| 1 | Task domain events via Dapr pub/sub | `backend/src/events.py` |
| 2 | Event emission on create / update / delete / toggle | `backend/src/routes/tasks.py` |
| 3 | Dapr pub/sub component (Kafka broker) | `dapr/components/kafka-pubsub.yaml` |
| 4 | Single-node Kafka (KRaft) for local dev | `k8s/kafka.yaml` |
| 5 | Dapr sidecar injection annotations | k8s & Helm backend manifests |
| 6 | DOKS-specific Helm values | `helm/todo-app/values-doks.yaml` |
| 7 | Automated DOKS deploy script | `scripts/deploy-doks.sh` |
| 8 | Tests for events module | `backend/tests/test_events.py` |

### Out of Scope (Phase V)

- Kafka consumers / subscribers (deferred — no consumer defined yet)
- Schema Registry or Avro serialisation
- Kafka UI or monitoring dashboard
- Multi-partition or multi-replica Kafka configuration
- Event sourcing or CQRS patterns
- DigitalOcean Managed Kafka (cost concern for hackathon)

---

## Event Schema

All events are published as JSON to the `task-events` topic on the `kafka-pubsub` Dapr component.

### Payload

```json
{
  "event_type": "task.created",
  "task_id": 42,
  "user_id": "usr_abc123",
  "timestamp": "2026-03-02T14:30:00.000Z",
  "title": "Buy milk"
}
```

### Event Types

| Event Type | Trigger | Extra Fields |
|-----------|---------|-------------|
| `task.created` | POST /api/tasks → 201 | `title` |
| `task.updated` | PUT /api/tasks/{id} → 200 | `title` |
| `task.deleted` | DELETE /api/tasks/{id} → 200 | — |
| `task.toggled` | PATCH /api/tasks/{id}/toggle → 200 | `completed` |

---

## Dapr Integration Architecture

```
FastAPI Route Handler
        │
        │  await publish_task_event("task.created", task.id, user_id)
        ▼
┌───────────────────────────────────────────────────────────┐
│  backend/src/events.py  (fail-soft publisher)             │
│                                                           │
│  POST http://localhost:{DAPR_HTTP_PORT}/v1.0/publish/     │
│       kafka-pubsub/task-events                            │
│                                                           │
│  • DAPR_HTTP_PORT not set → skip (log info)               │
│  • Connection refused / timeout → log warning, continue   │
│  • Non-2xx response → log warning, continue               │
└───────────────────────────────────────────────────────────┘
        │
        │  Dapr sidecar (port 3500)
        ▼
┌───────────────────────────────────────────────────────────┐
│  Dapr Pub/Sub component (kafka-pubsub)                    │
│  Component: dapr/components/kafka-pubsub.yaml             │
│  Broker: kafka-service:9092                               │
└───────────────────────────────────────────────────────────┘
        │
        │  Kafka producer
        ▼
┌───────────────────────────────────────────────────────────┐
│  Apache Kafka (KRaft, single node)                        │
│  Topic: task-events (auto-created)                        │
│  k8s/kafka.yaml — Deployment + Service                    │
└───────────────────────────────────────────────────────────┘
```

### Fail-Soft Design Principle

Events MUST NOT break the main request flow. If the Dapr sidecar is unreachable (non-Dapr deployment, sidecar crash, network issue):
- Log a `WARNING` with event_type, task_id, and exception
- The route handler continues and returns the normal HTTP response
- No HTTP 5xx, no retry loop, no exception propagation

This preserves backward compatibility: the app runs identically in Phase IV (Minikube, no Dapr) and Phase V (DOKS + Dapr).

---

## DOKS Deployment Architecture

```
Internet
    │
    ▼
DigitalOcean Load Balancer (provisioned by DOKS)
    │  http://todo.example.com
    ▼
nginx Ingress Controller
    │  /api/* → backend-service:8000
    │  /*     → frontend-service:3000
    ▼
┌─────────────────────────────────────┐
│  DOKS Cluster (2× s-2vcpu-4gb)      │
│                                     │
│  ┌──────────────────────────┐       │
│  │  backend Pod             │       │
│  │  ├── FastAPI container   │       │
│  │  └── Dapr sidecar        │       │
│  └──────────────────────────┘       │
│  ┌──────────────────────────┐       │
│  │  frontend Pod            │       │
│  │  └── Next.js container   │       │
│  └──────────────────────────┘       │
│  ┌──────────────────────────┐       │
│  │  kafka Pod               │       │
│  │  └── KRaft Kafka         │       │
│  └──────────────────────────┘       │
└─────────────────────────────────────┘
    │
    ▼
Neon DB (external managed PostgreSQL)
```

---

## Acceptance Criteria

| ID | Criterion | Test |
|----|-----------|------|
| **AC-P5-001** | `publish_task_event` succeeds when Dapr sidecar returns 204 | `test_events.py::test_publish_success` |
| **AC-P5-002** | `publish_task_event` logs a warning and does NOT raise when sidecar is unreachable | `test_events.py::test_publish_sidecar_unreachable_does_not_raise` |
| **AC-P5-003** | `publish_task_event` is a no-op when `DAPR_HTTP_PORT` env var is absent | `test_events.py::test_publish_skipped_when_dapr_not_configured` |
| **AC-P5-004** | `POST /api/tasks` calls `publish_task_event("task.created", ...)` after DB commit | `test_events.py::test_create_task_emits_event` |
| **AC-P5-005** | `DELETE /api/tasks/{id}` calls `publish_task_event("task.deleted", ...)` | `test_events.py::test_delete_task_emits_event` |
| **AC-P5-006** | All 246+ Phase I–IV tests still pass after Phase V changes | `uv run pytest tests/` |
| **AC-P5-007** | `dapr/components/kafka-pubsub.yaml` is valid Dapr component YAML | manual review |
| **AC-P5-008** | `helm/todo-app/values-doks.yaml` renders without errors with `helm lint` | `helm lint` |
| **AC-P5-009** | `scripts/deploy-doks.sh` documents all required env vars and steps | manual review |

---

## Files Changed / Created

| File | Change | Phase |
|------|--------|-------|
| `backend/src/events.py` | New — Dapr pub/sub publisher | V |
| `backend/src/routes/tasks.py` | Modified — emit events after mutations | V |
| `backend/tests/test_events.py` | New — AC-P5-001 through AC-P5-005 | V |
| `backend/pyproject.toml` | Modified — add `httpx>=0.27.0` | V |
| `dapr/components/kafka-pubsub.yaml` | New — Dapr Kafka pub/sub component | V |
| `k8s/kafka.yaml` | New — Single-node Kafka (KRaft) for dev | V |
| `k8s/backend-deployment.yaml` | Modified — Dapr sidecar annotations | V |
| `helm/todo-app/templates/backend-deployment.yaml` | Modified — Dapr sidecar annotations | V |
| `helm/todo-app/values-doks.yaml` | New — DOKS-specific values | V |
| `scripts/deploy-doks.sh` | New — DOKS automated deploy | V |
| `history/adr/002-phase-v-dapr-kafka-event-bus.md` | New — ADR | V |

---

## Non-Functional Requirements

| Concern | Requirement |
|---------|-------------|
| **Latency** | Event publishing adds ≤ 10 ms to route handler p95 (Dapr sidecar local) |
| **Reliability** | Single failed event publish never causes HTTP 5xx |
| **Security** | No Kafka credentials in git; injected via K8s Secret |
| **Backward compat** | App runs without Dapr/Kafka — Phase IV Minikube deploy unchanged |
| **Observability** | Every publish attempt logged at INFO (success) or WARNING (failure) |
