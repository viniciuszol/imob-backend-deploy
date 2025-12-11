# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base

from app.models.user import User
from app.models.user_empresa import UserEmpresa
from app.models.empresa import Empresa
from app.models.ativos import Ativo
from app.models.movimentacoes import Movimentacao
from app.models.cdi import CDI
from app.models.movimentacao_ativo import MovimentacaoAtivo
from app.models.investimento_cdi import InvestimentoCDI


from app.routers import (
    auth_router,
    ativos_router,
    movimentacoes_router,
    users_router,
    empresas_router,
    cdi_router,
    investimento_cdi_router,
)

app = FastAPI(title="ImobInvest API")

# ----------------------------------------------
# CORS — NECESSÁRIO para permitir POST do frontend
# ----------------------------------------------
origins = [
    "http://localhost:5173",   # Vite frontend
    "http://127.0.0.1:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # frontend permitido
    allow_credentials=True,
    allow_methods=["*"],         # <- ESSENCIAL para liberar OPTIONS
    allow_headers=["*"],         # <- ESSENCIAL
)

# Criar tabelas em dev
Base.metadata.create_all(bind=engine)

# Registrar rotas
app.include_router(auth_router.router)
app.include_router(users_router.router)
app.include_router(empresas_router.router)
app.include_router(ativos_router.router)
app.include_router(movimentacoes_router.router)
app.include_router(cdi_router.router)
app.include_router(investimento_cdi_router.router)
