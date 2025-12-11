from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.security import get_current_user
from app.models import User, Movimentacao, Ativo, UserEmpresa, MovimentacaoAtivo
from app import schemas

router = APIRouter(prefix="/movimentacoes", tags=["Movimentações"])


def user_has_access_to_ativo(db: Session, user_id: int, ativo_id: int) -> bool:
    ativo = db.query(Ativo).filter(Ativo.id == ativo_id).first()
    if not ativo:
        return False

    return (
        db.query(UserEmpresa)
        .filter_by(user_id=user_id, empresa_id=ativo.empresa_id)
        .first()
        is not None
    )


@router.get("/", response_model=list[schemas.MovimentacaoOut])
def list_movimentacoes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Movimentacao)
        .join(Ativo)
        .join(UserEmpresa, UserEmpresa.empresa_id == Ativo.empresa_id)
        .filter(UserEmpresa.user_id == current_user.id)
        .all()
    )


@router.get("/{mov_id}", response_model=schemas.MovimentacaoOut)
def get_movimentacao(
    mov_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    mov = db.query(Movimentacao).filter(Movimentacao.id == mov_id).first()
    if not mov:
        raise HTTPException(404, "Movimentação não encontrada")

    if not user_has_access_to_ativo(db, current_user.id, mov.ativo_id):
        raise HTTPException(403, "Acesso negado")

    return mov


@router.post("/", response_model=schemas.MovimentacaoOut)
def create_movimentacao(
    data: schemas.MovimentacaoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ativo = db.query(Ativo).filter(Ativo.id == data.ativo_id).first()
    if not ativo:
        raise HTTPException(400, "ativo_id inexistente")

    if not user_has_access_to_ativo(db, current_user.id, data.ativo_id):
        raise HTTPException(403, "Acesso negado ao ativo")

    mov = Movimentacao(**data.model_dump())
    db.add(mov)
    db.commit()
    db.refresh(mov)

    mov_ativo = MovimentacaoAtivo(
    movimentacao_id=mov.id,
    ativo_id=mov.ativo_id,
    valor=mov.valor,
    tipo="Recebimento" if mov.valor >= 0 else "Pagamento"
)
    db.add(mov_ativo)
    db.commit()

    return mov


@router.put("/{mov_id}", response_model=schemas.MovimentacaoOut)
def update_movimentacao(
    mov_id: int,
    data: schemas.MovimentacaoBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    mov = db.query(Movimentacao).filter(Movimentacao.id == mov_id).first()
    if not mov:
        raise HTTPException(404, "Movimentação não encontrada")

    if not user_has_access_to_ativo(db, current_user.id, mov.ativo_id):
        raise HTTPException(403, "Acesso negado")

    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(mov, k, v)

    db.commit()
    db.refresh(mov)
    return mov


@router.delete("/{mov_id}", response_model=schemas.MovimentacaoOut)
def delete_movimentacao(
    mov_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    mov = db.query(Movimentacao).filter(Movimentacao.id == mov_id).first()
    if not mov:
        raise HTTPException(404, "Movimentação não encontrada")

    if not user_has_access_to_ativo(db, current_user.id, mov.ativo_id):
        raise HTTPException(403, "Acesso negado")

    db.delete(mov)
    db.commit()

    return mov
