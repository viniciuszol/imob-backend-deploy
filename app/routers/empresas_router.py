# app/routers/empresas.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.security import get_current_user
from app.models import User, Empresa, UserEmpresa
from app.services.nibo_service import nibo_service
from app.services.nibo_import_service import nibo_import_service
from app.services.nibo_refresh_service import refresh_ativos
from app import schemas

router = APIRouter(prefix="/empresas", tags=["Empresas"])


def user_has_access(db: Session, user_id: int, empresa_id: int) -> bool:
    return (
        db.query(UserEmpresa)
        .filter_by(user_id=user_id, empresa_id=empresa_id)
        .first()
        is not None
    )


# ---------------------------------------------------------------------------
# CRIAR EMPRESA MANUAL
# ---------------------------------------------------------------------------
@router.post("/", response_model=schemas.EmpresaOut)
def create_empresa(
    empresa: schemas.EmpresaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_empresa = Empresa(
    nome=empresa.nome,
    cnpj=empresa.cnpj,
    nibo_company_id=empresa.nibo_company_id,
    usuario_id=current_user.id   # <<<<<<<<<<<<<< ESSENCIAL
)

    db.add(new_empresa)
    db.commit()
    db.refresh(new_empresa)

    db.add(UserEmpresa(user_id=current_user.id, empresa_id=new_empresa.id))
    db.commit()

    return new_empresa


# ---------------------------------------------------------------------------
#  IMPORTAÇÃO DO NIBO (o endpoint principal)
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
#  IMPORTAÇÃO DO NIBO (o endpoint principal)
# ---------------------------------------------------------------------------
@router.post("/importar")
async def importar_empresa(
    body: schemas.EmpresaImportToken,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    token = body.token

    # 1. Buscar perfil da empresa no Nibo
    try:
        profile = await nibo_service.get_empresa_profile(token)
    except Exception as e:
        raise HTTPException(400, f"Token Nibo inválido ou perfil inacessível: {str(e)}")

    # 2. Validar dados críticos
    if not profile.get("cnpj") or not profile.get("companyId"):
        raise HTTPException(
            400,
            "Perfil Nibo incompleto: CNPJ ou Company ID ausente."
        )

    # 3. Verifica se a empresa já existe para este usuário
    empresa = db.query(Empresa).filter(
        Empresa.cnpj == profile["cnpj"],
        Empresa.usuario_id == current_user.id
    ).first()

    if not empresa:
        # Se não existir, cria
        empresa = Empresa(
            nome=profile.get("nome", "Importada Nibo"),
            cnpj=profile.get("cnpj"),
            nibo_company_id=profile.get("companyId"),
            nibo_api_token=token,
            usuario_id=current_user.id
        )
        db.add(empresa)
        db.commit()
        db.refresh(empresa)
    else:
        # Se já existir, apenas atualiza o token
        empresa.nibo_api_token = token
        db.commit()
        db.refresh(empresa)

    empresa_data = {
        "nome": empresa.nome,
        "cnpj": empresa.cnpj,
        "companyId": empresa.nibo_company_id
    }

    # 4. Importar dados do Nibo usando o token
    resultado = await nibo_import_service.importar(
        db=db,
        token=token,
        usuario_id=current_user.id,
        empresa_data=empresa_data
    )

    return {
        "empresa": empresa,
        "resultado": resultado
    }

@router.post("/{empresa_id}/refresh")
async def refresh_empresa_ativos(empresa_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await refresh_ativos(db, current_user.id, empresa_id)
    return result

# ---------------------------------------------------------------------------
# LISTAGENS / CRUD mantidos
# ---------------------------------------------------------------------------
@router.put("/{empresa_id}", response_model=schemas.EmpresaOut)
def update_empresa(
    empresa_id: int,
    empresa_data: schemas.EmpresaUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        raise HTTPException(404, "Empresa não encontrada")

    if not user_has_access(db, current_user.id, empresa_id):
        raise HTTPException(403, "Acesso negado")

    for key, value in empresa_data.model_dump(exclude_unset=True).items():
        setattr(empresa, key, value)

    db.commit()
    db.refresh(empresa)

    return empresa

@router.delete("/{empresa_id}", response_model=schemas.EmpresaOut)
def delete_empresa(
    empresa_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        raise HTTPException(404, "Empresa não encontrada")

    if not user_has_access(db, current_user.id, empresa_id):
        raise HTTPException(403, "Acesso negado")

    db.delete(empresa)
    db.commit()

    return empresa
# ---------------------------------------------------------------------------
# LISTAGENS / CRUD ajustados
# ---------------------------------------------------------------------------

@router.get("/me", response_model=list[schemas.EmpresaOut])
def list_minhas_empresas(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Retorna todas as empresas vinculadas ao usuário
    return [ue.empresa for ue in current_user.empresas]


@router.get("/", response_model=list[schemas.EmpresaOut])
def list_empresas(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Pega IDs de empresas vinculadas ao usuário
    empresa_ids = [ue.empresa_id for ue in current_user.empresas]
    # Retorna apenas empresas vinculadas
    return db.query(Empresa).filter(Empresa.id.in_(empresa_ids)).all()


@router.get("/{empresa_id}", response_model=schemas.EmpresaPrivateOut)
def get_empresa(
    empresa_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Checa se o usuário tem acesso
    if not user_has_access(db, current_user.id, empresa_id):
        raise HTTPException(403, "Acesso negado")

    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        raise HTTPException(404, "Empresa não encontrada")

    return empresa



# ---------------------------------------------------------------------------
# Atualizar token do Nibo (AGORA CORRETO)
# ---------------------------------------------------------------------------
@router.put("/{empresa_id}/token-nibo", response_model=schemas.EmpresaPrivateOut)
def update_nibo_token(
    empresa_id: int,
    token: schemas.NiboTokenUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not user_has_access(db, current_user.id, empresa_id):
        raise HTTPException(403, "Acesso negado")

    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        raise HTTPException(404, "Empresa não encontrada")

    empresa.nibo_company_id = token.nibo_api_token  # agora é apitoken
    db.commit()
    db.refresh(empresa)

    return empresa


# ---------------------------------------------------------------------------
# ENDPOINTS DIRETOS DO NIBO (APENAS 4 QUE VOCÊ USA)
# ---------------------------------------------------------------------------

@router.get("/{empresa_id}/nibo/schedules")
async def nibo_schedules(
    empresa_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa or not empresa.nibo_company_id:
        raise HTTPException(400, "Token Nibo não configurado")

    return await nibo_service.get_schedules(empresa.nibo_company_id)


@router.get("/{empresa_id}/nibo/receipts")
async def nibo_receipts(empresa_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa or not empresa.nibo_company_id:
        raise HTTPException(400, "Token Nibo não configurado")

    return await nibo_service.get_receipts(empresa.nibo_company_id)


@router.get("/{empresa_id}/nibo/payments")
async def nibo_payments(empresa_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa or not empresa.nibo_company_id:
        raise HTTPException(400, "Token Nibo não configurado")

    return await nibo_service.get_payments(empresa.nibo_company_id)


@router.get("/{empresa_id}/nibo/costcenters")
async def nibo_costcenters(empresa_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa or not empresa.nibo_company_id:
        raise HTTPException(400, "Token Nibo não configurado")

    return await nibo_service.get_cost_centers(empresa.nibo_company_id)
    