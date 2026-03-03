# src/routes/auth.py — sign-up / sign-in endpoints
# Stores users in Neon DB (app_users table).
# Issues HS256 JWT tokens using the shared BETTER_AUTH_SECRET.

from __future__ import annotations

import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from src.database import get_session
from src.db_models import AppUser

router = APIRouter()

_SECRET: str = os.environ.get("BETTER_AUTH_SECRET", "dev-secret-change-in-production")
_ALGORITHM = "HS256"
_EXPIRY_DAYS = 7


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class SignUpRequest(BaseModel):
    name: str
    email: str
    password: str


class SignInRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    token: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    key = hashlib.scrypt(password.encode(), salt=salt.encode(), n=16384, r=8, p=1)
    return f"{salt}:{key.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        salt, key_hex = stored.split(":", 1)
        key = hashlib.scrypt(password.encode(), salt=salt.encode(), n=16384, r=8, p=1)
        return secrets.compare_digest(key.hex(), key_hex)
    except Exception:
        return False


def _make_token(user: AppUser) -> str:
    payload = {
        "sub": user.id,
        "email": user.email,
        "name": user.name,
        "exp": datetime.now(timezone.utc) + timedelta(days=_EXPIRY_DAYS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, _SECRET, algorithm=_ALGORITHM)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post("/sign-up", response_model=AuthResponse, status_code=201)
async def sign_up(
    body: SignUpRequest,
    session: Session = Depends(get_session),
) -> AuthResponse:
    name = body.name.strip()
    email = body.email.strip().lower()
    if not name:
        raise HTTPException(status_code=400, detail="Name is required.")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required.")
    if len(body.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")

    existing = session.exec(select(AppUser).where(AppUser.email == email)).first()
    if existing:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    user = AppUser(name=name, email=email, password_hash=_hash_password(body.password))
    session.add(user)
    session.commit()
    session.refresh(user)

    return AuthResponse(token=_make_token(user))


@router.post("/sign-in", response_model=AuthResponse)
async def sign_in(
    body: SignInRequest,
    session: Session = Depends(get_session),
) -> AuthResponse:
    email = body.email.strip().lower()
    user = session.exec(select(AppUser).where(AppUser.email == email)).first()

    if not user or not _verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    return AuthResponse(token=_make_token(user))
