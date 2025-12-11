# app/api/users.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.security import get_current_user, hash_password
from app import models, schemas

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me/profile", response_model=schemas.UserOut)
def get_my_profile(current_user: models.User = Depends(get_current_user)):
    return current_user


@router.put("/me/profile", response_model=schemas.UserOut)
def update_my_profile(
    user_data: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    data = user_data.dict(exclude_unset=True)

    # email lower e sem duplicidade
    if "email" in data:
        data["email"] = data["email"].lower()

        ja_existe = db.query(models.User).filter(
            models.User.email == data["email"],
            models.User.id != current_user.id
        ).first()

        if ja_existe:
            raise HTTPException(400, "Email já cadastrado por outro usuário")

    # atualizar senha
    if "password" in data:
        current_user.senha = hash_password(data.pop("password"))

    # atualizar demais campos
    for key, value in data.items():
        setattr(current_user, key, value)

    db.commit()
    db.refresh(current_user)
    return current_user

@router.post("/", response_model=schemas.UserOut)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    email = user.email.lower()

    db_user = db.query(models.User).filter(models.User.email == email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email já cadastrado")

    hashed = hash_password(user.password)

    new_user = models.User(
        nome=user.nome,
        email=email,
        senha=hashed
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.get("/", response_model=list[schemas.UserOut])
def get_users(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.User).all()


@router.get("/{user_id}", response_model=schemas.UserOut)
def get_user(user_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return user


@router.delete("/{user_id}", response_model=schemas.UserOut)
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    db.delete(user)
    db.commit()
    return user


@router.put("/{user_id}", response_model=schemas.UserOut)
def update_user(user_id: int, user_data: schemas.UserUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    data = user_data.dict(exclude_unset=True)

    # email lower e sem duplicidade
    if "email" in data:
        data["email"] = data["email"].lower()

        ja_existe = db.query(models.User).filter(
            models.User.email == data["email"],
            models.User.id != user_id
        ).first()

        if ja_existe:
            raise HTTPException(400, "Email já cadastrado por outro usuário")

    # senha
    if "password" in data:
        user.senha = hash_password(data.pop("password"))

    # demais campos
    for key, value in data.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return user
