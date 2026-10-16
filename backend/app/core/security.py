from functools import lru_cache

import jwt
from fastapi import Request

from app.core.config import Settings
from app.core.exceptions import AppError


@lru_cache
def _jwks(url: str) -> jwt.PyJWKClient:
    return jwt.PyJWKClient(url, cache_keys=True)


def get_subject(request: Request, settings: Settings) -> str:
    """Return the authenticated provider subject id, or raise 401."""
    if settings.auth_mode == "dev":  
        sub = request.headers.get("X-Dev-User", "").strip()
        if not sub:
            raise AppError(401, "unauthorized", "Missing X-Dev-User header.")
        return sub
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        raise AppError(401, "unauthorized", "Missing bearer token.")
    token = header[7:]
    try:
        key = _jwks(settings.clerk_jwks_url).get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token, key.key, algorithms=["RS256"], issuer=settings.clerk_issuer,
            options={"require": ["exp", "sub"], "verify_aud": False},
        )
    except jwt.PyJWTError as e:
        raise AppError(401, "unauthorized", "Invalid or expired token.") from e
    return claims["sub"]
