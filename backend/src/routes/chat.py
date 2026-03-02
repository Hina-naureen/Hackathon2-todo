# src/routes/chat.py — Phase III chat endpoint with TaskAgent tool calling
# References: specs/api/chat-endpoint.md §POST /api/chat
#             specs/agents/agent-behavior.md §Request Lifecycle
#             specs/features/chatbot.md §Functional Requirements

from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from agents.agent import ActionTrace, TaskAgent
from src.auth.dependencies import get_current_user
from src.database import get_session

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class ChatRequest(BaseModel):
    """Request body for POST /api/chat.

    References: specs/api/chat-endpoint.md §ChatRequest
    """

    message: str
    # Optional: YYYY-MM-DD string from the client so the agent can resolve
    # relative date phrases ("tomorrow", "next Friday") without ambiguity.
    today: str | None = None
    # When False, create_task is intercepted and returned as pending_task
    # without persisting — lets the frontend show a confirmation button.
    confirm: bool = True


class ActionTraceOut(BaseModel):
    """One tool invocation recorded during the request.

    References: specs/agents/agent-behavior.md §ActionTrace Type
    """

    tool: str
    args: dict[str, Any]
    result: Any


class ChatResponse(BaseModel):
    """Response body for POST /api/chat.

    References: specs/api/chat-endpoint.md §ChatResponse
    """

    reply: str
    trace_id: str
    actions: list[ActionTraceOut]
    # Populated when confirm=False and a create_task intent was detected.
    # Contains {title, description?, due_date?} for the frontend to render
    # a confirmation card without having persisted the task yet.
    pending_task: dict | None = None


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter()


@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    user_id: str = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> ChatResponse:
    """Run the TaskAgent for the authenticated user's message.

    Safe mode: if the agent raises for any reason (missing OPENAI_API_KEY,
    network error, unexpected exception) the error is logged and the route
    falls back to an echo reply so the API always returns 200.

    References: specs/agents/agent-behavior.md §Request Lifecycle
    """
    message = body.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    actions: list[ActionTrace] = []
    try:
        agent = TaskAgent(session, user_id)
        reply, actions = await agent.run(
            message, today=body.today, dry_run=not body.confirm
        )
    except Exception as exc:
        logger.error("Agent failed for user %s — falling back to echo: %s", user_id, exc)
        reply = f"You said: {message}"

    return ChatResponse(
        reply=reply,
        trace_id=str(uuid.uuid4()),
        actions=[
            ActionTraceOut(tool=a.tool, args=a.args, result=a.result)
            for a in actions
        ],
        pending_task=agent.pending_task,
    )
