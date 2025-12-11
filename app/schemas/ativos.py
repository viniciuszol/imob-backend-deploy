from app.schemas.movimentacao_ativo import MovimentacaoAtivoRead
from pydantic import BaseModel
from typing import Optional, List

from app.schemas.ativos_enums import (
    StatusAtivo,
    TipoAtivo,
    FinalidadeAtivo,
    GrauDesmobilizacaoAtivo,
    PotencialAtivo
)

class AtivoBase(BaseModel):
    nome: str
    empresa_id: int
    status: StatusAtivo
    tipo: TipoAtivo
    finalidade: FinalidadeAtivo
    potencial: PotencialAtivo
    grau_desmobilizacao: GrauDesmobilizacaoAtivo

    nibo_cost_center_id: Optional[str] = None

    percentual_participacao: float
    valor_compra: float
    gastos: Optional[float] = None
    receita: Optional[float] = None

    saldo_devedor: Optional[float] = None
    preco_venda: Optional[float] = None
    participacao_venda: Optional[float] = None

    ativo: bool

class AtivoCreate(AtivoBase):
    pass


class AtivoUpdate(BaseModel):
    nome: Optional[str] = None
    status: Optional[StatusAtivo] = None
    tipo: Optional[TipoAtivo] = None
    finalidade: Optional[FinalidadeAtivo] = None
    potencial: Optional[PotencialAtivo] = None
    grau_desmobilizacao: Optional[GrauDesmobilizacaoAtivo] = None

    percentual_participacao: Optional[float] = None
    valor_compra: Optional[float] = None
    gastos: Optional[float] = None
    receita: Optional[float] = None

    saldo_devedor: Optional[float] = None
    preco_venda: Optional[float] = None
    participacao_venda: Optional[float] = None

    ativo: bool

class AtivoOut(AtivoBase):
    id: int
    total: Optional[float] = None
    movimentacao_ativos: Optional[List[MovimentacaoAtivoRead]] = []

    model_config = {"from_attributes": True}