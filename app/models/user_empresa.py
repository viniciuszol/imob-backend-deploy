from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class UserEmpresa(Base):
    __tablename__ = "usuarios_empresas"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    empresa_id = Column(Integer, ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)

    user = relationship("User", back_populates="empresas")
    empresa = relationship("Empresa", back_populates="usuarios")

    __table_args__ = (UniqueConstraint("user_id", "empresa_id", name="uix_user_empresa"),)

    def __repr__(self):
        return f"<UserEmpresa user={self.user_id} empresa={self.empresa_id}>"
