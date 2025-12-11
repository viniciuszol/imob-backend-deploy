from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Empresa(Base):
    __tablename__ = "empresas"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

    # Interno
    nome = Column(String, nullable=False)
    cnpj = Column(String, unique=True, nullable=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())

    # Identificação no Nibo
    nibo_company_id = Column(String, unique=True, nullable=True)   # <--- NOVO
    nibo_api_token = Column(String, nullable=True)


    # relationships
    usuarios = relationship("UserEmpresa", back_populates="empresa", cascade="all, delete-orphan")
    ativos = relationship("Ativo", back_populates="empresa", cascade="all, delete-orphan")    

    def __repr__(self):
        return f"<Empresa {self.id} - {self.nome}>"
