# app/schemas/empresa.py
from app.schemas.movimentacoes import MovimentacaoOut
from app.schemas.ativos import AtivoOut
from pydantic import BaseModel
from typing import Optional, List

class EmpresaResumoOut(BaseModel):
    id: int
    nome: str
    cnpj: str | None = None

    model_config = {"from_attributes": True}


class EmpresaCreate(BaseModel):
    nome: str
    cnpj: Optional[str] = None
    nibo_company_id: Optional[str] = None  # apitoken


class EmpresaOut(BaseModel):
    id: int
    nome: str
    cnpj: Optional[str] = None
    nibo_company_id: Optional[str] = None  # apitoken

    model_config = {"from_attributes": True}


class EmpresaPrivateOut(EmpresaOut):
    """
    Versão privada da empresa, usada internamente.
    Mantém o nibo_company_id visível.
    """
    model_config = {"from_attributes": True}


class EmpresaUpdate(BaseModel):
    nome: Optional[str] = None
    cnpj: Optional[str] = None
    nibo_company_id: Optional[str] = None  # apitoken


class EmpresaImportacaoIn(BaseModel):
    """
    Recebe um apitoken do Nibo (que vamos armazenar em nibo_company_id).
    Pode:
    - Criar empresa + importar (nome, cnpj, nibo_company_id)
    - Importar para empresa existente (empresa_id)
    """
    empresa_id: Optional[int] = None
    nome: Optional[str] = None
    cnpj: Optional[str] = None

    # APITOKEN
    nibo_company_id: Optional[str] = None

    model_config = {"from_attributes": True}


class EmpresaImportacaoOut(BaseModel):
    empresa: EmpresaOut
    ativos: List[AtivoOut]
    movimentacoes: List[MovimentacaoOut]

    model_config = {"from_attributes": True}

class NiboTokenUpdate(BaseModel):
    nibo_company_id: str

class EmpresaImportToken(BaseModel):
    token: str