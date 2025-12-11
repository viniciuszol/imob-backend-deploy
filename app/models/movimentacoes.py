from sqlalchemy import Column, Integer, ForeignKey, Date, Numeric, String
from sqlalchemy.orm import relationship
from app.database import Base

class Movimentacao(Base):
    __tablename__ = "movimentacoes"

    id = Column(Integer, primary_key=True, index=True)
    ativo_id = Column(Integer, ForeignKey("ativos.id", ondelete="CASCADE"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)


    # ID da Nibo (quando forem transações da API)
    nibo_transaction_id = Column(String, unique=True, nullable=True)
    
    data_movimentacao = Column(Date, nullable=False)
    descricao = Column(String, nullable=True)

    valor = Column(Numeric(12, 2), nullable=False)
    investimento = Column(Numeric(12, 2), nullable=True)
    rendimento_cdi = Column(Numeric(12, 2), nullable=True)
    saldo_cdi = Column(Numeric(12, 2), nullable=True)
    diferenca = Column(Numeric(12, 2), nullable=True)

    ativo = relationship("Ativo", back_populates="movimentacoes")

    movimentacao_ativos = relationship(
    "MovimentacaoAtivo", 
    back_populates="movimentacao",
    cascade="all, delete-orphan"
)


    def __repr__(self):
        return f"<Movimentacao {self.id} - ativo={self.ativo_id} valor={self.valor}>"
