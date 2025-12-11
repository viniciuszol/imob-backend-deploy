from datetime import datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.core.deps import get_db
from app.core.security import get_current_user
from app.models import User, Ativo, UserEmpresa
router = APIRouter(prefix="/ativos", tags=["Ativos"])


def user_has_access(db: Session, user_id: int, empresa_id: int) -> bool:
    return (
        db.query(UserEmpresa)
        .filter_by(user_id=user_id, empresa_id=empresa_id)
        .first()
        is not None
    )


@router.get("/", response_model=list[schemas.AtivoOut])
def list_ativos(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return (
        db.query(Ativo)
        .join(UserEmpresa, UserEmpresa.empresa_id == Ativo.empresa_id)
        .filter(UserEmpresa.user_id == current_user.id)
        .all()
    )


@router.get("/{ativo_id}", response_model=schemas.AtivoOut)
def get_ativo(
    ativo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ativo = db.query(Ativo).filter(Ativo.id == ativo_id).first()
    if not ativo:
        raise HTTPException(404, "Ativo não encontrado")

    if not user_has_access(db, current_user.id, ativo.empresa_id):
        raise HTTPException(403, "Acesso negado ao ativo")

    return ativo


@router.post("/", response_model=schemas.AtivoOut)
def create_ativo(
    ativo: schemas.AtivoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not user_has_access(db, current_user.id, ativo.empresa_id):
        raise HTTPException(403, "Acesso negado à empresa")

    new_ativo = Ativo(**ativo.model_dump())
    db.add(new_ativo)
    db.commit()
    db.refresh(new_ativo)

    return new_ativo


@router.put("/{ativo_id}", response_model=schemas.AtivoOut)
def update_ativo(
    ativo_id: int,
    ativo_data: schemas.AtivoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ativo = db.query(Ativo).filter(Ativo.id == ativo_id).first()
    if not ativo:
        raise HTTPException(404, "Ativo não encontrado")

    if not user_has_access(db, current_user.id, ativo.empresa_id):
        raise HTTPException(403, "Acesso negado ao ativo")

    dados = ativo_data.model_dump(exclude_unset=True)

    for key, value in dados.items():
        if key == "total":
            continue  # total é calculado no banco
        setattr(ativo, key, value)

    db.commit()
    db.refresh(ativo)
    return ativo



@router.delete("/{ativo_id}", response_model=schemas.AtivoOut)
def delete_ativo(
    ativo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ativo = db.query(Ativo).filter(Ativo.id == ativo_id).first()
    if not ativo:
        raise HTTPException(404, "Ativo não encontrado")

    if not user_has_access(db, current_user.id, ativo.empresa_id):
        raise HTTPException(403, "Acesso negado ao ativo")

    db.delete(ativo)
    db.commit()

    return ativo

@router.get("/{ativo_id}/comparativo")
def comparativo_ativo(
    ativo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.models import Ativo, UserEmpresa, InvestimentoCDI

    ativo = db.query(Ativo).filter(Ativo.id == ativo_id).first()
    if not ativo:
        raise HTTPException(404, "Ativo não encontrado")

    if not db.query(UserEmpresa).filter_by(user_id=current_user.id, empresa_id=ativo.empresa_id).first():
        raise HTTPException(403, "Acesso negado ao ativo")

    # pegar dados básicos
    valor_inicial = ativo.valor_inicial
    data_inicio = ativo.data_inicio
    data_fim = ativo.data_fim or datetime.utcnow().date()

    # cálculo CDI SIMPLIFICADO
    dias = (data_fim - data_inicio).days
    cdi_dia = Decimal("0.00036")  # exemplo
    rendimento_percentual = (1 + cdi_dia) ** dias - 1
    rendimento_valor = valor_inicial * rendimento_percentual

    # salva no BD (mínimo possíve)
    registro = InvestimentoCDI(
        ativo_id=ativo_id,
        data=data_fim,
        valor_inicial=valor_inicial,
        valor_final=valor_inicial + rendimento_valor,
        rendimento_percentual=rendimento_percentual,
        rendimento_valor=rendimento_valor
    )

    db.add(registro)
    db.commit()
    db.refresh(registro)

    return {
        "ativo_id": ativo_id,
        "dias": dias,
        "cdi_percentual": rendimento_percentual,
        "rendimento_valor": rendimento_valor,
        "valor_final_cdi": valor_inicial + rendimento_valor
    }
