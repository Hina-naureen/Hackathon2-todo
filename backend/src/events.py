# backend/src/events.py — Phase V: Dapr pub/sub event publisher
# References: specs/phase5-dapr-kafka.md §Dapr Integration Architecture
#             specs/phase5-dapr-kafka.md §Event Schema
#
# Design: fail-soft.
#   If the Dapr sidecar is absent (DAPR_HTTP_PORT not set) or unreachable,
#   a WARNING is logged and the caller continues normally. Events must never
#   break the main request path.
#
# Activation:
#   Dapr injects DAPR_HTTP_PORT automatically when the sidecar is present.
#   No manual configuration is needed in Dapr-annotated pods.
#   Set DAPR_HTTP_PORT="" or leave it unset in non-Dapr deployments.

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration (injected by Dapr sidecar in annotated pods)
# ---------------------------------------------------------------------------

_DAPR_HTTP_PORT: str | None = os.environ.get("DAPR_HTTP_PORT")
_PUBSUB_NAME: str = os.environ.get("DAPR_PUBSUB_NAME", "kafka-pubsub")
_TOPIC: str = os.environ.get("DAPR_TOPIC", "task-events")
_TIMEOUT_S: float = 2.0  # Dapr sidecar is local; 2 s is generous


def _dapr_enabled() -> bool:
    """Return True only when the Dapr sidecar port is configured.

    Dapr injects DAPR_HTTP_PORT into the app container when the pod carries
    the dapr.io/enabled: "true" annotation. In bare Minikube or local dev
    the variable is absent, so publishing is silently skipped.
    """
    return bool(_DAPR_HTTP_PORT)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def publish_task_event(
    event_type: str,
    task_id: int,
    user_id: str,
    extra: dict[str, Any] | None = None,
) -> None:
    """Publish a task lifecycle event to Kafka via the Dapr sidecar.

    References: specs/phase5-dapr-kafka.md §AC-P5-001 through §AC-P5-003

    Args:
        event_type: One of "task.created", "task.updated", "task.deleted",
                    "task.toggled".
        task_id: Primary key of the affected task.
        user_id: Authenticated user who triggered the mutation.
        extra: Optional additional fields merged into the payload
               (e.g. {"title": "Buy milk"} or {"completed": True}).

    Raises:
        Never. All errors are caught and logged as WARNING.
    """
    if not _dapr_enabled():
        logger.debug(
            "Dapr not configured (DAPR_HTTP_PORT unset) — skipping %s for task %d",
            event_type,
            task_id,
        )
        return

    payload: dict[str, Any] = {
        "event_type": event_type,
        "task_id": task_id,
        "user_id": user_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **(extra or {}),
    }

    url = (
        f"http://localhost:{_DAPR_HTTP_PORT}"
        f"/v1.0/publish/{_PUBSUB_NAME}/{_TOPIC}"
    )

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_S) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
        logger.info(
            "Published %s for task %d (user=%s)", event_type, task_id, user_id
        )
    except Exception as exc:
        logger.warning(
            "Dapr publish failed — event_type=%s task_id=%d: %s — continuing",
            event_type,
            task_id,
            exc,
        )
