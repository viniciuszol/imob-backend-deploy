# app/models/investimento_cdi.py
from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    Numeric,
    Date,
    SmallInteger,
    DateTime,
    func,
)
from sqlalchemy.orm import relationship
from app.database import Base


class InvestimentoCDI(Base):
    __tablename__ = "investimento_cdi"

    id = Column(Integer, primary_key=True, index=True)
    ativo_id = Column(
        Integer,
        ForeignKey("ativos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    valor_compra_ativo = Column(Numeric(18, 2), nullable=False)

    # sempre 1º dia do mês; DB permite NULL, mas na prática vamos SEMPRE preencher
    data = Column(Date, nullable=True, index=True)

    rendimento_cdi_mes = Column(Numeric(18, 4), nullable=True, default=0)
    rendimento_cdi_acumulado = Column(Numeric(18, 4), nullable=True, default=0)
    diferenca_rendimento = Column(Numeric(18, 4), nullable=True)

    # fator decimal: ex 0.0076 (0,76% ao mês)
    cdi_mes = Column(Numeric(10, 6), nullable=True, default=0)

    ano = Column(SmallInteger, nullable=True)
    mes = Column(SmallInteger, nullable=True)

    criado_em = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=True,
    )
    atualizado_em = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=True,
        onupdate=func.now(),
    )

    ativo = relationship("Ativo", back_populates="investimentos_cdi")
