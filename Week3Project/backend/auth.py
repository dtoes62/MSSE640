"""
JWT authentication — token creation, verification, and the /auth/token endpoint.

Pattern:
  POST /auth/token  {username, password}  →  {access_token, token_type, expires_in}
  Every protected request must carry:     Authorization: Bearer <access_token>
"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

import config

# ---------------------------------------------------------------------------
# Crypto helpers
# ---------------------------------------------------------------------------

_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def _verify_password(plain: str, hashed: str) -> bool:
    return _pwd_ctx.verify(plain, hashed)


# ---------------------------------------------------------------------------
# Token creation / verification
# ---------------------------------------------------------------------------

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = config.ACCESS_TOKEN_EXPIRE_MINUTES * 60


def create_access_token(data: dict) -> str:
    """Return a signed JWT containing *data* plus an expiry claim."""
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload["exp"] = expire
    payload["iat"] = datetime.now(timezone.utc)
    return jwt.encode(payload, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)


def verify_token(token: str) -> dict:
    """
    Decode and validate *token*.

    Raises jose.JWTError (or subclass) if the token is invalid or expired —
    callers should catch this and return HTTP 401.
    """
    return jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])


# ---------------------------------------------------------------------------
# /auth/token router
# ---------------------------------------------------------------------------

auth_router = APIRouter(tags=["Authentication"])


@auth_router.post(
    "/token",
    response_model=TokenResponse,
    summary="Obtain a JWT Bearer token",
    description=(
        "Submit your username and password to receive a short-lived JWT. "
        "Include the token as `Authorization: Bearer <token>` on every GraphQL request."
    ),
)
def login(form: OAuth2PasswordRequestForm = Depends()) -> TokenResponse:
    hashed = config.DEMO_USERS.get(form.username)
    if not hashed or not _verify_password(form.password, hashed):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token({"sub": form.username})
    return TokenResponse(access_token=token)
