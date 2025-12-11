# app/models/movimentacao_ativo.py
from sqlalchemy import Column, Integer, Numeric, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.ativos import Ativo
from app.models.movimentacoes import Movimentacao

class MovimentacaoAtivo(Base):
    __tablename__ = "movimentacao_ativo"

    id = Column(Integer, primary_key=True, index=True)
    movimentacao_id = Column(Integer, ForeignKey("movimentacoes.id", ondelete="CASCADE"), nullable=False)
    ativo_id = Column(Integer, ForeignKey("ativos.id", ondelete="CASCADE"), nullable=False)
    valor = Column(Numeric(12, 2), nullable=False, default=0)
    tipo = Column(String, nullable=False)  # Recebimento / Pagamento / Agendamento
    criado_em = Column(DateTime(timezone=True), server_default=func.now())

    # Relações
    movimentacao = relationship("Movimentacao", back_populates="movimentacao_ativos")
    ativo = relationship("Ativo", back_populates="movimentacao_ativos")
