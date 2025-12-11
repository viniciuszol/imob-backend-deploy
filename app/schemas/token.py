# app/schemas/token.py
from pydantic import BaseModel, Field
from typing import List
from .empresa import EmpresaResumoOut

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

    model_config = {
        "from_attributes": True
    }

class TokenWithEmpresas(Token):
    email: str
    nome: str
    empresas: List[EmpresaResumoOut] = Field(default_factory=list)

    model_config = {
        "from_attributes": True
    }
