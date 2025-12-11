# app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session, joinedload
from datetime import timedelta, datetime
from typing import Optional

from app import models, schemas
from app.core.deps import get_db
from app.core.security import verify_password, create_access_token, hash_password, get_current_user
from app.models import User

router = APIRouter(prefix="/auth", tags=["Auth"])

# Simple in-memory brute-force mitigation
_login_attempts: dict[str, dict] = {}
MAX_ATTEMPTS = 5
LOCK_SECONDS = 300  # 5 minutos de bloqueio após exceder tentativas

def _register_failed_attempt(username: str):
    entry = _login_attempts.get(username) or {"count": 0, "first_at": datetime.utcnow(), "locked_until": None}
    entry["count"] += 1
    if entry["count"] >= MAX_ATTEMPTS:
        entry["locked_until"] = datetime.utcnow() + timedelta(seconds=LOCK_SECONDS)
    _login_attempts[username] = entry

def _is_locked(username: str) -> bool:
    entry = _login_attempts.get(username)
    if not entry:
        return False
    locked_until = entry.get("locked_until")
    if locked_until:
        if datetime.utcnow() < locked_until:
            return True
        entry["count"] = 0
        entry["locked_until"] = None
        _login_attempts[username] = entry
    return False

def _clear_attempts(username: str):
    if username in _login_attempts:
        del _login_attempts[username]

# ---------------------------
# LOGIN (resolvendo o erro)
# ---------------------------
# ---------------------------
# LOGIN (corrigido)
# ---------------------------
@router.post("/login", response_model=schemas.TokenWithEmpresas)
def login(
    body: schemas.LoginSchema,
    db: Session = Depends(get_db),
):
    email = body.email.lower()
    password = body.password

    if _is_locked(email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas tentativas. Tente novamente mais tarde."
        )

    # ✅ Carrega o usuário junto com as empresas associadas
    user = db.query(models.User).options(
        joinedload(models.User.empresas).joinedload(models.UserEmpresa.empresa)
    ).filter(models.User.email == email).first()

    if not user or not verify_password(password, user.senha):
        _register_failed_attempt(email)
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Conta desativada")

    _clear_attempts(email)

    token_payload = {"sub": str(user.id), "role": user.role}
    access_token = create_access_token(
        data=token_payload,
        expires_delta=timedelta(hours=3)
    )

    empresas_resumo = [
        schemas.EmpresaResumoOut.from_orm(ue.empresa)
        for ue in user.empresas
        if ue.empresa is not None
    ]

    return schemas.TokenWithEmpresas(
        access_token=access_token,
        token_type="bearer",
        email=user.email,
        nome=user.nome,
        empresas=empresas_resumo
    )




# ---------------------------
# REGISTER
# ---------------------------
@router.post("/register", response_model=schemas.UserOut)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email já cadastrado")

    hashed = hash_password(user_in.password)
    new_user = User(nome=user_in.nome, email=user_in.email, senha=hashed)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# ---------------------------
# GET ME
# ---------------------------
@router.get("/me", response_model=schemas.UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

# ---------------------------
# REFRESH TOKEN
# ---------------------------
@router.post("/refresh", response_model=schemas.Token)
def refresh_token(current_user: User = Depends(get_current_user)):
    access_token = create_access_token(
        data={"sub": str(current_user.id), "role": getattr(current_user, "role", "user")},
        expires_delta=timedelta(hours=3)
    )
    return {"access_token": access_token, "token_type": "bearer"}
