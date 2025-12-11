# app/schemas/investimento_cdi.py
from pydantic import BaseModel
from decimal import Decimal
from datetime import date, datetime


class InvestimentoCDIBase(BaseModel):
    ativo_id: int
    valor_compra_ativo: Decimal
    data: date | None = None  # se vier None, DB/trigger tenta inferir pelo ativo


class InvestimentoCDICreate(InvestimentoCDIBase):
    pass


class InvestimentoCDIUpdate(BaseModel):
    valor_compra_ativo: Decimal | None = None
    data: date | None = None
    # normalmente esses campos são calculados pela trigger, mas vou deixar editável opcional
    rendimento_cdi_mes: Decimal | None = None
    rendimento_cdi_acumulado: Decimal | None = None
    diferenca_rendimento: Decimal | None = None
    cdi_mes: Decimal | None = None


class InvestimentoCDIOut(BaseModel):
    id: int
    ativo_id: int
    valor_compra_ativo: Decimal
    data: date | None

    ano: int | None = None
    mes: int | None = None

    rendimento_cdi_mes: Decimal | None = None
    rendimento_cdi_acumulado: Decimal | None = None
    diferenca_rendimento: Decimal | None = None
    cdi_mes: Decimal | None = None

    criado_em: datetime | None = None
    atualizado_em: datetime | None = None

    class Config:
        from_attributes = True
