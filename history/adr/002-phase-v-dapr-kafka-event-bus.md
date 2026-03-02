# ADR-002: Phase V — Dapr + Kafka Event Bus Strategy

**Date:** 2026-03-02
**Status:** Accepted
**Deciders:** Hackathon II Team
**References:** specs/phase5-dapr-kafka.md §Dapr Integration Architecture

---

## Context

Phase V requires an event-driven backbone so every task mutation (create / update / delete / toggle) emits a domain event for future consumers (audit logs, notifications, real-time sync). Three interconnected decisions were made:

1. Which message broker to use
2. How to decouple the backend from the broker
3. How to handle the case where the event system is unavailable

---

## Decision 1 — Apache Kafka (KRaft) as the message broker

### Options Considered

| Option | Durability | Operational complexity |
|--------|-----------|------------------------|
| **Apache Kafka** | Durable log, ordered per-partition | Higher: needs dedicated cluster |
| RabbitMQ | Message-level ACK, per-queue ordering | Medium: stateful, needs management plugin |
| Redis Streams | In-memory with optional AOF | Low: single binary, but not durable by default |
| NATS JetStream | Very low latency | Low maturity in enterprise use cases |

### Decision

**Apache Kafka 3.7 in KRaft mode** (no ZooKeeper) as the pub/sub broker.

### Rationale

- Kafka is the **locked tech choice** in `.specify/memory/constitution.md §II`.
- KRaft mode (Kafka 3.x) eliminates the ZooKeeper dependency, reducing the dev cluster from 2 deployments to 1.
- Kafka's durable, ordered log is ideal for task audit trails — events can be replayed by future consumers.
- For dev/Minikube: single-node `k8s/kafka.yaml`. For DOKS production: same manifest or Strimzi operator.

### Consequences

- Kafka pod requires ~512 Mi RAM — acceptable for a `s-2vcpu-4gb` DOKS node.
- Topic auto-creation is enabled for dev (`KAFKA_AUTO_CREATE_TOPICS_ENABLE=true`). Pre-create topics in production.
- `k8s/kafka.yaml` uses `emptyDir` volumes — data is lost on pod restart. Production deployments should use a PVC or managed Kafka.

---

## Decision 2 — Dapr pub/sub sidecar as the broker abstraction

### Options Considered

| Option | Broker coupling | Added complexity |
|--------|----------------|-----------------|
| **Dapr pub/sub HTTP API** | None — component YAML swaps broker | Dapr operator install |
| `kafka-python` / `aiokafka` direct | Hard-wired to Kafka | Simple (one library) |
| Confluent Python client | Hard-wired + licence concerns | More features than needed |

### Decision

**Dapr sidecar + pub/sub component**, called via Dapr's HTTP API (`POST localhost:3500/v1.0/publish/...`).

### Rationale

- **Broker portability**: swapping Kafka for RabbitMQ or Redis Streams only requires changing `dapr/components/kafka-pubsub.yaml` — no Python code changes.
- **Dapr is the locked tech** for Phase V per the constitution.
- The HTTP API (`localhost:3500`) is language-agnostic and adds no Python dependency.
- Dapr injects `DAPR_HTTP_PORT` automatically into the app container when the pod annotation `dapr.io/enabled: "true"` is present — zero configuration needed in application code.

### Consequences

- Dapr operator must be installed in the cluster before deploying the app:
  `helm install dapr dapr/dapr -n dapr-system --create-namespace`
- Each backend pod gains a `daprd` sidecar container (~50 Mi RAM, ~10 m CPU at idle).
- Without Dapr, the `events.py` module operates in silent no-op mode (see Decision 3).

---

## Decision 3 — Fail-soft design: events never break requests

### Problem

Task mutations (POST/PUT/DELETE/PATCH /api/tasks) must succeed even if:
- The cluster runs without Dapr (Phase IV Minikube deployment, local dev)
- The Dapr sidecar crashes or restarts
- Kafka is temporarily unavailable

### Decision

`src/events.py` is **fail-soft**:
1. If `DAPR_HTTP_PORT` env var is absent → skip publishing, log at DEBUG level.
2. If the HTTP call raises any exception (connection refused, timeout, non-2xx) → log at WARNING level, continue normally.

```python
# No DAPR_HTTP_PORT → immediate return, no network call
if not _dapr_enabled():
    return

try:
    async with httpx.AsyncClient(timeout=2.0) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
except Exception as exc:
    logger.warning("Dapr publish failed — ... %s — continuing", exc)
```

### Rationale

- **Backward compatibility**: Phase IV Minikube deployment continues to work unchanged (no `DAPR_HTTP_PORT` → no-op).
- **Resilience**: a Dapr sidecar crash during a task operation does not cause HTTP 5xx to the user.
- **Observability**: every failed publish attempt is logged at WARNING — operators can alert on this.
- **Testability**: `DAPR_HTTP_PORT` is monkeypatched in tests; `httpx.AsyncClient` is mocked.

### Consequences

- Events are fire-and-forget with no retry. A failed publish is **not re-attempted**.
  - Accepted for Phase V (hackathon scope). Production systems should use a dead-letter queue or outbox pattern.
- `httpx` is now an explicit production dependency (was transitive via `fastapi[standard]`).
- `pytest-asyncio` is now a dev dependency for testing async event functions.

---

## Summary

| Decision | Choice | Key Benefit |
|----------|--------|-------------|
| Message broker | Kafka 3.7 KRaft (single-node) | Durable log, matches constitution tech stack |
| Broker abstraction | Dapr pub/sub HTTP API | Broker-agnostic; `DAPR_HTTP_PORT` detection |
| Failure handling | Fail-soft: log + continue | Phase IV compat; no HTTP 5xx on Dapr issues |
