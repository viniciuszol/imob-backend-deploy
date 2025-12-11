# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Nibo base (token por empresa é armazenado no DB)
    NIBO_API_BASE: str = "https://api.nibo.com.br"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
