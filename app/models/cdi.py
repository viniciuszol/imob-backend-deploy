from sqlalchemy import Column, Integer, Date, Numeric
from app.database import Base

class CDI(Base):
    __tablename__ = "cdi"

    id = Column(Integer, primary_key=True, index=True)
    data = Column(Date, nullable=False, unique=True)

    porcentagem = Column(Numeric(5, 2), default=100)  # ex: 100%
    cdi_am = Column(Numeric(8, 5))                    # 100% CDI ao mês
    cdi_percentual_am = Column(Numeric(8, 5))         # CDI% a.m.

    def __repr__(self):
        return f"<CDI {self.data} - {self.cdi_percentual_am}>"
