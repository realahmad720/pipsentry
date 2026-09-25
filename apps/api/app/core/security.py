"""Clerk session-token verification.

Every authenticated request carries a Clerk-issued JWT in the Authorization
header. We verify it against Clerk's JWKS and resolve it to our own `users`
row (creating one on first sight), so every downstream query can be scoped
by our internal user_id rather than trusting a client-supplied id.
"""

import uuid

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import get_db
from app.models.user import User

_bearer = HTTPBearer(auto_error=False)
_jwks_cache: dict | None = None


def _get_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache is None:
        if not settings.clerk_jwks_url:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR, "CLERK_JWKS_URL is not configured"
            )
        response = httpx.get(settings.clerk_jwks_url, timeout=5.0)
        response.raise_for_status()
        _jwks_cache = response.json()
    return _jwks_cache


def _decode_clerk_token(token: str) -> dict:
    try:
        header = jwt.get_unverified_header(token)
        jwks = _get_jwks()
        key = next((k for k in jwks["keys"] if k["kid"] == header["kid"]), None)
        if key is None:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unknown signing key")
        return jwt.decode(token, key, algorithms=[header["alg"]], options={"verify_aud": False})
    except HTTPException:
        raise
    except Exception as exc:  # invalid signature, expired token, malformed JWT, etc.
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid session token") from exc


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")

    claims = _decode_clerk_token(credentials.credentials)
    auth_provider_id: str = claims["sub"]
    email: str | None = claims.get("email")

    user = db.query(User).filter(User.auth_provider_id == auth_provider_id).one_or_none()
    if user is None:
        user = User(
            id=uuid.uuid4(),
            email=email or f"{auth_provider_id}@unknown.pipsentry",
            auth_provider_id=auth_provider_id,
            plan_tier="free",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return user
