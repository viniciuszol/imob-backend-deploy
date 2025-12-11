from pydantic import BaseModel

class UserEmpresaBase(BaseModel):
    user_id: int
    empresa_id: int

class UserEmpresaCreate(UserEmpresaBase):
    pass

class UserEmpresaOut(UserEmpresaBase):
    id: int

    model_config = {
        "from_attributes": True
    }
