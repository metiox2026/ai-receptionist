"""Auth — minimal JWT-based login. Real RBAC enforced in the API, not just UI."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import get_settings
from api.db import get_session
from api.models import User
from api.schemas import LoginIn, TokenOut, UserCreate, UserOut

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings()


def _hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def _verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _issue_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "iat": int(datetime.now(tz=timezone.utc).timestamp()),
        "exp": int(datetime.now(tz=timezone.utc).timestamp()) + 60 * 60 * 24,
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def signup(payload: UserCreate, session: AsyncSession = Depends(get_session)) -> User:
    existing = await session.scalar(select(User).where(User.email == payload.email))
    if existing:
        raise HTTPException(status_code=409, detail="email already registered")
    user = User(
        email=payload.email,
        password_hash=_hash_password(payload.password),
        role=payload.role,
        # business_id set in the seed script; first signup is the owner.
        business_id="00000000-0000-0000-0000-000000000000",
    )
    session.add(user)
    await session.flush()
    return user


@router.post("/login", response_model=TokenOut)
async def login(form: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_session)) -> TokenOut:
    user = await session.scalar(select(User).where(User.email == form.username))
    if not user or not _verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="invalid credentials")
    return TokenOut(access_token=_issue_token(str(user.id)))


@router.post("/login-json", response_model=TokenOut)
async def login_json(payload: LoginIn, session: AsyncSession = Depends(getSession)) -> TokenOut:
    """Convenience JSON login for the dashboard."""
    user = await session.scalar(select(User).where(User.email == payload.email))
    if not user or not _verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="invalid credentials")
    return TokenOut(access_token=_issue_token(str(user.id)))


def decode_token(token: str) -> str:
    """Helper used by other routers to get the user id from a JWT."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="invalid token") from exc
    return payload["sub"]