# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base

# MODELS (importados para garantir criação das tabelas)
from app.models.user import User
from app.models.user_empresa import UserEmpresa
from app.models.empresa import Empresa
from app.models.ativos import Ativo
from app.models.movimentacoes import Movimentacao
from app.models.cdi import CDI
from app.models.movimentacao_ativo import MovimentacaoAtivo
from app.models.investimento_cdi import InvestimentoCDI

# ROUTERS
from app.routers import (
    auth_router,
    ativos_router,
    movimentacoes_router,
    users_router,
    empresas_router,
    cdi_router,
    investimento_cdi_router,
)

# SEED
from app.seeds.cdi_seed import seed_cdi


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
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------------------------
# STARTUP EVENT
# ----------------------------------------------
@app.on_event("startup")
def on_startup():
    try:
        # Garante que as tabelas existam (DEV)
        Base.metadata.create_all(bind=engine)

        # Executa seed de CDI (idempotente)
        seed_cdi()

    except Exception as e:
        print(f"❌ Erro no startup da aplicação: {e}")
        # Impede subir backend em estado inconsistente
        raise


# ----------------------------------------------
# Registrar rotas
# ----------------------------------------------
app.include_router(auth_router.router)
app.include_router(users_router.router)
app.include_router(empresas_router.router)
app.include_router(ativos_router.router)
app.include_router(movimentacoes_router.router)
app.include_router(cdi_router.router)
app.include_router(investimento_cdi_router.router)
