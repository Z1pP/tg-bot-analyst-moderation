import time
from functools import lru_cache
from pathlib import Path
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config import settings

AUTH_SCHEME = HTTPBearer(auto_error=False)
SERVICE_AUD = "backend"


@lru_cache
def _load_pub_key() -> str:
    path = Path(settings.SERVICE_BOT_PUBLIC_KEY_PATH)
    return path.read_text()


def verify_service_jwt(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(AUTH_SCHEME)],
):
    if not creds:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="missing token"
        )
    try:
        claims = jwt.decode(
            creds.credentials,
            _load_pub_key(),
            algorithms=["RS256"],
            audience=SERVICE_AUD,
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token"
        )
    if claims.get("role") != "bot":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    if claims.get("exp", 0) < time.time():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="expired")
    return claims


ServiceAuth = Annotated[dict, Depends(verify_service_jwt)]
