from pydantic import BaseModel, Field, field_validator
from decimal import Decimal
from datetime import date
from typing import Optional, List
from app.schemas.movimentacao_ativo import MovimentacaoAtivoRead

class MovimentacaoBase(BaseModel):
    data_movimentacao: date

    descricao: Optional[str] = None
    valor: Decimal  # removido ge=0

    investimento: Optional[Decimal] = None
    rendimento_cdi: Optional[Decimal] = None
    saldo_cdi: Optional[Decimal] = None
    diferenca: Optional[Decimal] = None

    # 🔥 Removido o bloqueio de datas futuras
    # Agora aceita qualquer data

    @field_validator("descricao")
    @classmethod
    def limpar_descricao(cls, v: Optional[str]):
        if v is None:
            return None
        v = v.strip()
        return v if v else None


class MovimentacaoCreate(MovimentacaoBase):
    ativo_id: int
    nibo_transaction_id: Optional[str] = None


class MovimentacaoOut(MovimentacaoBase):
    id: int
    ativo_id: int
    nibo_transaction_id: Optional[str] = None
    movimentacao_ativos: Optional[List[MovimentacaoAtivoRead]] = []
    @property
    def tipo(self):
        if self.valor is None:
            return None
        return "entrada" if self.valor >= 0 else "saida"
    
    model_config = {"from_attributes": True}


class MovimentacaoUpdate(BaseModel):
    data_movimentacao: Optional[date] = None

    descricao: Optional[str] = None
    valor: Optional[Decimal] = None

    investimento: Optional[Decimal] = None
    rendimento_cdi: Optional[Decimal] = None
    saldo_cdi: Optional[Decimal] = None
    diferenca: Optional[Decimal] = None


    @field_validator("descricao")
    @classmethod
    def limpar_descricao(cls, v: Optional[str]):
        if v is None:
            return None
        v = v.strip()
        return v if v else None
