from __future__ import annotations

from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette import status

from .config import get_settings


bearer_scheme = HTTPBearer(auto_error=False)


def admin_auth(credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme)) -> None:
    settings = get_settings()
    token = credentials.credentials if credentials else None
    if not token or token != settings.admin_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "unauthorized", "message": "Invalid or missing admin token", "details": {}},
        )


