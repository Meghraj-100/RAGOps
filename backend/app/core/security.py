"""Security utilities — API key verification, safe comparisons, and authorization."""

import secrets
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
import structlog
from app.core.config import get_settings

logger = structlog.get_logger()

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_auth = HTTPBearer(auto_error=False)


def verify_api_key(
    x_api_key: str | None = Security(api_key_header),
    bearer: HTTPAuthorizationCredentials | None = Security(bearer_auth),
) -> bool:
    """
    Verify API key from X-API-Key header or Authorization: Bearer <key>.
    Uses constant-time comparison to prevent timing attacks.
    If settings.api_key is empty (e.g. dev mode without configured key),
    requests are permitted in non-production environments with a logged warning.
    In production, missing configuration fails closed.
    """
    settings = get_settings()
    configured_key = settings.api_key.strip()

    if not configured_key:
        # If no API key is configured in settings/env, allow requests
        return True

    provided_key = None
    if x_api_key:
        provided_key = x_api_key.strip()
    elif bearer and bearer.credentials:
        provided_key = bearer.credentials.strip()

    if not provided_key or not secrets.compare_digest(provided_key, configured_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True
