from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.core.deps import get_db
from app.models import InvestimentoCDI, Movimentacao, Ativo, CDI
from app.schemas import investimento_cdi as schemas
from app.schemas.ativos import AtivoOut

router = APIRouter(prefix="/investimentos", tags=["Investimentos"])


# ----------------------------------------------------
# LISTAGEM BÁSICA
# ----------------------------------------------------
@router.get("/", response_model=list[schemas.InvestimentoCDIOut])
def list_investimento_cdi(db: Session = Depends(get_db)):
    return db.query(InvestimentoCDI).all()


@router.get("/ativo/{ativo_id}", response_model=list[schemas.InvestimentoCDIOut])
def get_investimento_cdi_ativo(ativo_id: int, db: Session = Depends(get_db)):
    return (
        db.query(InvestimentoCDI)
        .filter(InvestimentoCDI.ativo_id == ativo_id)
        .order_by(InvestimentoCDI.data)
        .all()
    )


# ----------------------------------------------------
# CRUD
# ----------------------------------------------------
@router.post("/", response_model=schemas.InvestimentoCDIOut)
def create_investimento_cdi(
    payload: schemas.InvestimentoCDICreate,
    db: Session = Depends(get_db),
):
    data = payload.data.replace(day=1) if payload.data else None

    obj = InvestimentoCDI(
        ativo_id=payload.ativo_id,
        valor_compra_ativo=payload.valor_compra_ativo,
        data=data,
        ano=data.year if data else None,
        mes=data.month if data else None,
    )

    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/{id}", response_model=schemas.InvestimentoCDIOut)
def update_investimento_cdi(
    id: int,
    payload: schemas.InvestimentoCDIUpdate,
    db: Session = Depends(get_db),
):
    obj = db.query(InvestimentoCDI).filter(InvestimentoCDI.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Investimento CDI não encontrado")

    update_data = payload.model_dump(exclude_unset=True)

    if "data" in update_data and update_data["data"]:
        update_data["data"] = update_data["data"].replace(day=1)
        update_data["ano"] = update_data["data"].year
        update_data["mes"] = update_data["data"].month

    for key, value in update_data.items():
        setattr(obj, key, value)

    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{id}", response_model=schemas.InvestimentoCDIOut)
def delete_investimento_cdi(id: int, db: Session = Depends(get_db)):
    obj = db.query(InvestimentoCDI).filter(InvestimentoCDI.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Investimento CDI não encontrado")

    db.delete(obj)
    db.commit()
    return obj


# ----------------------------------------------------
# NOVAS ROTAS — PARA A TELA DE INVESTIMENTOS
# ----------------------------------------------------

# ---------------------------
# 1. REAL do ativo
# ---------------------------
@router.get("/real/{ativo_id}")
def get_real_do_ativo(ativo_id: int, db: Session = Depends(get_db)):
    movs = (
        db.query(Movimentacao)
          .filter(Movimentacao.ativo_id == ativo_id)
          .order_by(Movimentacao.data_movimentacao)
          .all()
    )

    resultado = []
    acumulado = 0

    for m in movs:
        valor = float(m.valor or 0)
        acumulado += valor

        resultado.append({
            "data": m.data_movimentacao.replace(day=1),
            "valor": valor,
            "acumulado": acumulado
        })

    return resultado


# ---------------------------
# 2. Comparativo CDI x REAL
# ---------------------------
@router.get("/comparativo/{ativo_id}")
def comparativo_cdi_real(ativo_id: int, db: Session = Depends(get_db)):
    # puxar o ativo para pegar o total
    ativo = db.query(Ativo).filter(Ativo.id == ativo_id).first()
    total_ativo = float(ativo.total or 0)

    cdi_rows = (
        db.query(InvestimentoCDI)
        .filter(InvestimentoCDI.ativo_id == ativo_id)
        .order_by(InvestimentoCDI.data)
        .all()
    )

    movs = (
        db.query(Movimentacao)
        .filter(Movimentacao.ativo_id == ativo_id)
        .all()
    )

    real_map = {}
    for m in movs:
        mes = m.data_movimentacao.replace(day=1)
        real_map.setdefault(mes, 0)
        real_map[mes] += float(m.valor or 0)

    comparativo = []
    real_acum = 0

    for linha in cdi_rows:
        mes = linha.data
        real_mes = real_map.get(mes, 0)
        real_acum += real_mes

        comparativo.append({
            "data": mes,
            "valor_compra_ativo": float(linha.valor_compra_ativo),
            "cdi_mes": float(linha.cdi_mes or 0),
            "rent_cdi": float(linha.rendimento_cdi_mes or 0),
            "rent_cdi_acum": float(linha.rendimento_cdi_acumulado or 0),

            "rent_real": real_mes,
            "rent_real_acum": real_acum,

            "diferenca": real_mes - float(linha.rendimento_cdi_mes or 0),

            # 🔥 campo novo — agora o front consegue pegar!
            "total_ativo": total_ativo
        })

    return comparativo



# ---------------------------
# 3. Lista de ativos (select)
# ---------------------------
@router.get("/ativos", response_model=list[AtivoOut])
def lista_ativos(db: Session = Depends(get_db)):
    return db.query(Ativo).order_by(Ativo.nome).all()

# ---------------------------
# 4. Enums para filtros
# ---------------------------
@router.get("/enums")
def get_enums():
    from app.schemas.ativos_enums import (
        StatusAtivo, TipoAtivo, FinalidadeAtivo,
        GrauDesmobilizacaoAtivo, PotencialAtivo
    )

    return {
        "status": [s.value for s in StatusAtivo],
        "tipo": [t.value for t in TipoAtivo],
        "finalidade": [f.value for f in FinalidadeAtivo],
        "grau_desmobilizacao": [g.value for g in GrauDesmobilizacaoAtivo],
        "potencial": [p.value for p in PotencialAtivo],
    }

# ----------------------------------------------------
# 5. OVERVIEW — para pizza e filtros
# ----------------------------------------------------
@router.get("/overview")
def investimentos_overview(
    status: str | None = None,
    tipo: str | None = None,
    finalidade: str | None = None,
    grau_desmobilizacao: str | None = None,
    potencial: str | None = None,
    db: Session = Depends(get_db)
):

    query = db.query(Ativo)

    if status:
        query = query.filter(Ativo.status == status)

    if tipo:
        query = query.filter(Ativo.tipo == tipo)

    if finalidade:
        query = query.filter(Ativo.finalidade == finalidade)

    if grau_desmobilizacao:
        query = query.filter(Ativo.grau_desmobilizacao == grau_desmobilizacao)

    if potencial:
        query = query.filter(Ativo.potencial == potencial)

    ativos = query.all()

    lista = []
    total_geral = 0

    for a in ativos:
        valor = float(a.total or 0)
        lista.append({
            "id": a.id,
            "nome": a.nome,
            "total": valor
        })
        total_geral += valor

    return {
        "total_geral": total_geral,
        "ativos": lista
    }


# ----------------------------------------------------
# 6. EVOLUÇÃO DO CDI — gráfico puro
# ----------------------------------------------------
@router.get("/evolucao-cdi")
def evolucao_cdi(db: Session = Depends(get_db)):
    cdis = db.query(CDI).order_by(CDI.data).all()

    return [
        {
            "data": c.data,
            "cdi": float(c.cdi_am or 0)
        }
        for c in cdis
    ]
