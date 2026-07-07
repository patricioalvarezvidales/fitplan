import uuid
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models import User

settings = get_settings()
password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_v1_prefix}/auth/login")


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)


def create_token(user: User, purpose: str = "access", minutes: int | None = None) -> str:
    expires = datetime.now(UTC) + timedelta(minutes=minutes or settings.access_token_expire_minutes)
    payload = {
        "sub": str(user.id),
        "ver": user.token_version,
        "purpose": purpose,
        "exp": expires,
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido o vencido") from exc


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    payload = decode_token(token)
    if payload.get("purpose") != "access":
        raise HTTPException(status_code=401, detail="Token inválido")
    user = db.scalar(select(User).where(User.id == uuid.UUID(payload.get("sub"))))
    if not user or not user.is_active or user.token_version != payload.get("ver"):
        raise HTTPException(status_code=401, detail="Sesión inválida")
    return user
