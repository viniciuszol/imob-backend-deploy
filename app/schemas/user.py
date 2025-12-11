from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional

class UserBase(BaseModel):
    nome: Optional[str] = Field(None, min_length=1)
    email: Optional[EmailStr] = None

    model_config = {
        "from_attributes": True
    }

class UserCreate(UserBase):
    nome: str = Field(..., min_length=1)
    email: EmailStr
    password: str = Field(..., min_length=3)

    @field_validator("email")
    def email_para_minusculo(cls, v: str):
        return v.lower()
    
class LoginSchema(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=1)
    email: Optional[EmailStr] = None
    password: Optional[str] = None

    @field_validator("email")
    def email_para_minusculo(cls, v):
        return v.lower() if v else v

class UserOut(UserBase):
    id: int

    model_config = {
        "from_attributes": True
    }
