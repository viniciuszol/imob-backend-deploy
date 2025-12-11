# app/schemas/movimentacao_ativo.py
from pydantic import BaseModel
from datetime import datetime

class MovimentacaoAtivoBase(BaseModel):
    movimentacao_id: int
    ativo_id: int
    valor: float
    tipo: str

class MovimentacaoAtivoCreate(MovimentacaoAtivoBase):
    pass

class MovimentacaoAtivoRead(MovimentacaoAtivoBase):
    id: int
    criado_em: datetime

    class Config:
        orm_mode = True
