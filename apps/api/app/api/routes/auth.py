import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import (
    create_token,
    decode_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.db.session import get_db
from app.models import User
from app.schemas.api import LoginRequest, MeOut, RegisterRequest, RegisterResponse, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=RegisterResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> RegisterResponse:
    email = payload.email.lower().strip()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="El correo ya está registrado")
    user = User(name=payload.name.strip(), email=email, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_token(user, purpose="confirm", minutes=60 * 24)
    return RegisterResponse(message="Cuenta creada. Confirma tu correo para continuar.", confirmation_token=token)


@router.post("/confirm-email")
def confirm_email(token: str, db: Session = Depends(get_db)) -> dict[str, str]:
    payload = decode_token(token)
    if payload.get("purpose") != "confirm":
        raise HTTPException(status_code=400, detail="Token de confirmación inválido")
    user = db.scalar(select(User).where(User.id == uuid.UUID(payload.get("sub"))))
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    user.email_confirmed = True
    db.commit()
    return {"message": "Correo confirmado correctamente"}


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email.lower().strip()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")
    if not user.email_confirmed:
        raise HTTPException(status_code=403, detail="Confirma tu correo antes de iniciar sesión")
    return TokenResponse(access_token=create_token(user))


@router.get("/me", response_model=MeOut)
def me(user: User = Depends(get_current_user)) -> MeOut:
    return MeOut(
        id=user.id,
        name=user.name,
        email=user.email,
        email_confirmed=user.email_confirmed,
        profile_complete=user.profile is not None,
    )


@router.post("/logout")
def logout(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, str]:
    user.token_version += 1
    db.commit()
    return {"message": "Sesión cerrada"}
