from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from decimal import Decimal

from app.services.nibo_service import nibo_service, fetch_all_pages, fetch_all
from app.services import investimento_cdi_service
from app.models import Empresa, Ativo, Movimentacao, UserEmpresa, MovimentacaoAtivo
from app.schemas.ativos_enums import (
    StatusAtivo,
    TipoAtivo,
    FinalidadeAtivo,
    GrauDesmobilizacaoAtivo,
    PotencialAtivo,
)


# ----------------------------------------
# Helpers
# ----------------------------------------
def parse_date(v):
    if not v:
        return datetime.today().date()
    try:
        cleaned = v.replace("Z", "")
        return datetime.fromisoformat(cleaned).date()
    except:
        return datetime.today().date()


def parse_decimal(v):
    try:
        if isinstance(v, str):
            v = v.replace(",", ".")
        return Decimal(str(v))
    except:
        return Decimal("0")


def _normalize_nibo_key(val):
    """
    Normaliza o valor do costCenterId para map:
    None → "None"
    dict → extrai id
    inteiro/string → str
    """
    if val is None:
        return "None"
    if isinstance(val, dict):
        v = val.get("costCenterId") or val.get("id")
        return _normalize_nibo_key(v)
    try:
        return str(val).strip()
    except:
        return "None"


# ----------------------------------------
# Serviço principal
# ----------------------------------------
class NiboImportService:

    async def importar(self, db: Session, token: str, usuario_id: int, empresa_data: dict):

        # -----------------------------
        # EMPRESA
        # -----------------------------
        empresa = db.query(Empresa).filter(
            Empresa.cnpj == empresa_data["cnpj"],
            Empresa.usuario_id == usuario_id
        ).first()

        if not empresa:
            empresa = Empresa(
                usuario_id=usuario_id,
                nome=empresa_data["nome"],
                cnpj=empresa_data["cnpj"],
                nibo_company_id=empresa_data.get("companyId"),
                nibo_api_token=token
            )
            db.add(empresa)
            db.commit()
            db.refresh(empresa)
        else:
            empresa.nibo_api_token = token
            db.commit()
            db.refresh(empresa)

        # vínculo user–empresa
        if not db.query(UserEmpresa).filter_by(user_id=usuario_id, empresa_id=empresa.id).first():
            db.add(UserEmpresa(user_id=usuario_id, empresa_id=empresa.id))
            db.commit()

        # -----------------------------
        # COST CENTERS → ATIVOS
        # -----------------------------
        try:
            costcenters = await fetch_all(token, nibo_service.get_costcenters)
        except Exception:
            costcenters = []

        map_ativos = {}

        existentes_query = db.query(Ativo).filter(
            Ativo.empresa_id == empresa.id,
            Ativo.usuario_id == usuario_id
        ).all()

        existentes_map = {
            _normalize_nibo_key(a.nibo_cost_center_id): a.id
            for a in existentes_query
        }

        unique_nibo_keys = set()

        for cc in costcenters:
            nibo_id = None
            nome = None

            if isinstance(cc, dict):
                nibo_id = (
                    cc.get("costCenterId")
                    or cc.get("id")
                    or cc.get("costCenterID")
                    or cc.get("centerId")
                )
                nome = (
                    cc.get("description")
                    or cc.get("name")
                    or cc.get("title")
                )
                if nibo_id is None:
                    nested = cc.get("costCenter") or cc.get("cost_center")
                    if isinstance(nested, dict):
                        nibo_id = nested.get("id") or nested.get("costCenterId")
            else:
                nibo_id = cc

            key = _normalize_nibo_key(nibo_id)
            unique_nibo_keys.add(key)

            if not nome:
                nome = "Centro sem nome"

            ativo_existente = db.query(Ativo).filter(
                Ativo.nibo_cost_center_id == nibo_id,
                Ativo.empresa_id == empresa.id,
                Ativo.usuario_id == usuario_id
            ).first()

            if ativo_existente:
                if not ativo_existente.ativo:
                    continue
                map_ativos[key] = ativo_existente.id
                continue

            try:
                ativo = Ativo(
                    usuario_id=usuario_id,
                    empresa_id=empresa.id,
                    nome=nome,
                    status=StatusAtivo.vazio,
                    tipo=TipoAtivo.residencial,
                    finalidade=FinalidadeAtivo.locacao_venda,
                    grau_desmobilizacao=GrauDesmobilizacaoAtivo.moderado,
                    potencial=PotencialAtivo.medio,
                    percentual_participacao=100,
                    valor_compra=0,
                    gastos=0,
                    receita=0,
                    saldo_devedor=None,
                    preco_venda=None,
                    participacao_venda=100,
                    nibo_cost_center_id=nibo_id
                )
                db.add(ativo)
                db.flush()
                map_ativos[key] = ativo.id
                existentes_map[key] = ativo.id

            except IntegrityError:
                db.rollback()
                existing = db.query(Ativo).filter(
                    Ativo.nibo_cost_center_id == nibo_id
                ).first()
                if existing:
                    map_ativos[key] = existing.id
                    existentes_map[key] = existing.id
                else:
                    continue
            except Exception:
                db.rollback()
                continue

        ativo_sem_cc = db.query(Ativo).filter_by(
            usuario_id=usuario_id,
            empresa_id=empresa.id,
            nibo_cost_center_id=None
        ).first()

        if not ativo_sem_cc:
            ativo_sem_cc = Ativo(
                usuario_id=usuario_id,
                empresa_id=empresa.id,
                nome="SEM CENTRO DE CUSTO",
                status=StatusAtivo.vazio,
                tipo=TipoAtivo.residencial,
                finalidade=FinalidadeAtivo.locacao_venda,
                grau_desmobilizacao=GrauDesmobilizacaoAtivo.moderado,
                potencial=PotencialAtivo.medio,
                percentual_participacao=100,
                valor_compra=0,
                gastos=0,
                receita=0,
                saldo_devedor=None,
                preco_venda=None,
                participacao_venda=100,
                nibo_cost_center_id=None
            )
            db.add(ativo_sem_cc)
            db.flush()

        map_ativos["None"] = ativo_sem_cc.id

        # ----------------------------------------
        # Funções de parsing
        # ----------------------------------------
        def extract_nibo_cc_from_costcenters_field(cc_field):
            if not cc_field:
                return "None"

            if isinstance(cc_field, list) and len(cc_field) > 0:
                first = cc_field[0]
                if isinstance(first, dict):
                    nid = first.get("costCenterId") or first.get("id") or first.get("centerId")
                    return _normalize_nibo_key(nid)
                return _normalize_nibo_key(first)

            if isinstance(cc_field, dict):
                nid = cc_field.get("costCenterId") or cc_field.get("id") or cc_field.get("centerId")
                return _normalize_nibo_key(nid)

            return _normalize_nibo_key(cc_field)

        # ----------------------------------------
        # PARSER DE MOVIMENTAÇÕES
        # ----------------------------------------
        def parse_movimentos(data_list, tipo="Recebimento"):
            for item in data_list:
                if not isinstance(item, dict):
                    continue

                # ✅ CORREÇÃO DEFINITIVA
                # somente movimentações com isTransfer == False entram
                if item.get("isTransfer") is not False:
                    continue

                cc_field = (
                    item.get("costCenters")
                    or item.get("costCenter")
                    or item.get("cost_centers")
                )
                key = extract_nibo_cc_from_costcenters_field(cc_field)
                ativo_id = map_ativos.get(key, ativo_sem_cc.id)

                data_raw = (
                    item.get("date")
                    or item.get("dueDate")
                    or item.get("accrualDate")
                )

                valor_raw = item.get("value") or item.get("amount") or 0
                nibo_id = item.get("entryId") or item.get("id")

                existente = db.query(Movimentacao).filter(
                    Movimentacao.usuario_id == usuario_id,
                    Movimentacao.nibo_transaction_id == nibo_id
                ).first()

                valor = parse_decimal(valor_raw)
                if tipo == "Pagamento":
                    valor = -valor

                data_mov = parse_date(data_raw)

                if existente:
                    if not db.query(MovimentacaoAtivo).filter_by(
                        movimentacao_id=existente.id,
                        ativo_id=ativo_id
                    ).first():
                        db.add(MovimentacaoAtivo(
                            movimentacao_id=existente.id,
                            ativo_id=ativo_id,
                            valor=valor,
                            tipo=tipo
                        ))
                    continue

                mov = Movimentacao(
                    usuario_id=usuario_id,
                    ativo_id=ativo_id,
                    data_movimentacao=data_mov,
                    descricao=item.get("identifier") or item.get("description") or tipo,
                    valor=valor,
                    investimento=0,
                    rendimento_cdi=0,
                    saldo_cdi=0,
                    diferenca=0,
                    nibo_transaction_id=nibo_id
                )
                db.add(mov)
                db.flush()

                db.add(MovimentacaoAtivo(
                    movimentacao_id=mov.id,
                    ativo_id=ativo_id,
                    valor=valor,
                    tipo=tipo
                ))
                db.flush()

                ativo = db.query(Ativo).filter_by(id=ativo_id).first()
                if ativo:
                    if valor >= 0:
                        ativo.receita = (ativo.receita or 0) + valor
                    else:
                        ativo.gastos = (ativo.gastos or 0) + valor
                    db.add(ativo)

        # ----------------------------------------
        # RECEBIMENTOS
        # ----------------------------------------
        try:
            receipts = await fetch_all_pages(nibo_service.get_receipts, token)
        except Exception:
            receipts = []

        parse_movimentos(receipts, "Recebimento")

        # ----------------------------------------
        # PAGAMENTOS
        # ----------------------------------------
        try:
            payments = await fetch_all_pages(nibo_service.get_payments, token)
        except Exception:
            payments = []

        parse_movimentos(payments, "Pagamento")

        db.commit()

        # ----------------------------------------
        # CÁLCULO DO CDI
        # ----------------------------------------
        try:
            investimento_cdi_service.recalcular_investimentos_cdi_empresa(db, empresa.id)
        except Exception as e:
            print("Erro ao recalcular investimentos CDI na importação:", e)

        ativos_importados = (
            len([k for k in unique_nibo_keys if k != "None"]) + 1
        )

        return {
            "status": "ok",
            "empresa_id": empresa.id,
            "empresa_nome": empresa.nome,
            "ativos_importados": ativos_importados,
            "movimentacoes_importadas": len(receipts) + len(payments)
        }


nibo_import_service = NiboImportService()
