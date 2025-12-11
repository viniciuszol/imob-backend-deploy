from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, Numeric, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.schema import Computed
from app.database import Base

from app.schemas.ativos_enums import (
    StatusAtivo,
    TipoAtivo,
    FinalidadeAtivo,
    GrauDesmobilizacaoAtivo,
    PotencialAtivo
)

class Ativo(Base):
    __tablename__ = "ativos"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)


    # ID da Nibo
    nibo_cost_center_id = Column(String, unique=True, nullable=True)

    nome = Column(String, nullable=False)

    status = Column(Enum(StatusAtivo, name="status_ativo"), nullable=False)
    tipo = Column(Enum(TipoAtivo, name="tipo_ativo"), nullable=False)
    finalidade = Column(Enum(FinalidadeAtivo, name="finalidade_ativo"), nullable=False)
    potencial = Column(Enum(PotencialAtivo, name="potencial_ativo"), nullable=False)
    grau_desmobilizacao = Column(Enum(GrauDesmobilizacaoAtivo, name="grau_desmobilizacao_ativo"), nullable=False)

    percentual_participacao = Column(Numeric(10, 2), nullable=False)

    valor_aquisicao = Column(Numeric(10, 2), nullable=False, default=0)
    despesas_aquisicao = Column(Numeric(10, 2), nullable=False, default=0)
    valor_compra = Column(Numeric(12, 2), nullable=False)
    gastos = Column(Numeric(12, 2), nullable=True)
    receita = Column(Numeric(12, 2), nullable=True)

    total = Column(Numeric(12, 2), Computed("COALESCE(receita, 0) + COALESCE(gastos, 0)", persisted=True))

    saldo_devedor = Column(Numeric(12, 2), nullable=True)
    preco_venda = Column(Numeric(12, 2), nullable=True)
    participacao_venda = Column(Numeric(12, 2), nullable=True)

    ativo = Column(Boolean, default=True)

    empresa = relationship("Empresa", back_populates="ativos")
    movimentacoes = relationship("Movimentacao", back_populates="ativo", cascade="all, delete-orphan")
    investimentos_cdi = relationship("InvestimentoCDI", back_populates="ativo", cascade="all, delete-orphan")
    

    movimentacao_ativos = relationship(
    "MovimentacaoAtivo", 
    back_populates="ativo",
    cascade="all, delete-orphan"
)

    def __repr__(self):
        return f"<Ativo {self.id} - {self.nome}>"
    
    __mapper_args__ = {
    "eager_defaults": True
}

