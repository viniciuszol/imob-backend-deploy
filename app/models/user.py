from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    senha = Column(String, nullable=False)  

    is_active = Column(Boolean, default=True, nullable=False)
    role = Column(String, default="user", nullable=False)

    empresas = relationship("UserEmpresa", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.id} - {self.email}>"

    def verify_password(self, password: str) -> bool:
        from app.core.security import verify_password
        return verify_password(password, self.senha) 
