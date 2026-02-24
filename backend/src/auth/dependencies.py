# src/auth/dependencies.py — JWT verification middleware skeleton
# References: specs/features/authentication.md §Better Auth Configuration
#             specs/api/rest-endpoints.md §Error Taxonomy

from __future__ import annotations

import os

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# Load .env early so BETTER_AUTH_SECRET is available regardless of import order.
load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Shared secret — must match the BETTER_AUTH_SECRET in frontend/.env.local.
# Set via backend/.env before deploying. The default is dev-only.
BETTER_AUTH_SECRET: str = os.environ.get(
    "BETTER_AUTH_SECRET", "dev-secret-change-in-production"
)

# When AUTH_DISABLED=true, get_current_user returns "dev-user" without
# validating any token. Use ONLY in local development, never in production.
AUTH_DISABLED: bool = os.environ.get("AUTH_DISABLED", "false").lower() == "true"

_bearer = HTTPBearer(auto_error=False)

# ---------------------------------------------------------------------------
# Dependency
# ---------------------------------------------------------------------------


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str:
    """Extract and validate the Better Auth JWT; return the user_id (sub claim).

    Raises HTTP 401 for missing, expired, or invalid tokens.

    TODO: When the Next.js frontend is running, Better Auth issues signed JWTs.
          This function decodes them using the shared BETTER_AUTH_SECRET.
          No changes required here once Better Auth is configured.
    """
    if AUTH_DISABLED:
        return "dev-user"

    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated.")

    try:
        payload: dict = jwt.decode(
            credentials.credentials,
            BETTER_AUTH_SECRET,
            algorithms=["HS256"],
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired.")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token.")

    user_id: str | None = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token.")

    return user_id
