from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from decimal import Decimal
from typing import List, Dict, Any

from app.models import Empresa, Ativo, Movimentacao, MovimentacaoAtivo, UserEmpresa
from app.schemas.ativos_enums import (
    StatusAtivo,
    TipoAtivo,
    FinalidadeAtivo,
    GrauDesmobilizacaoAtivo,
    PotencialAtivo,
)
from app.services.investimento_cdi_service import recalcular_investimentos_cdi_empresa
from app.services.nibo_service import nibo_service, fetch_all_pages, fetch_all


# -----------------------
# Helpers
# -----------------------
def _normalize_nibo_key(val) -> str:
    if val is None:
        return "None"
    if isinstance(val, dict):
        v = val.get("costCenterId") or val.get("id")
        return _normalize_nibo_key(v)
    try:
        return str(val).strip()
    except:
        return "None"


def _extract_costcenter_id_from_item(item: Dict[str, Any]):
    """
    Retorna o primeiro costCenterId encontrado no item (ou None).
    """
    if not item:
        return None
    cc_field = item.get("costCenters") or item.get("costCenter") or item.get("cost_centers")
    if not cc_field:
        return None
    if isinstance(cc_field, list) and len(cc_field) > 0:
        first = cc_field[0]
        if isinstance(first, dict):
            return first.get("costCenterId") or first.get("id") or first.get("centerId")
        return first
    if isinstance(cc_field, dict):
        return cc_field.get("costCenterId") or cc_field.get("id") or cc_field.get("centerId")
    return cc_field


def _to_decimal(v) -> Decimal:
    if v is None:
        return Decimal("0")
    try:
        if isinstance(v, str):
            v = v.replace(",", ".")
        return Decimal(str(v))
    except:
        return Decimal("0")


# -----------------------
# Serviço principal
# -----------------------
async def refresh_ativos(db: Session, user_id: int, empresa_id: int):

    # --------------- permissões ---------------
    if not db.query(UserEmpresa).filter_by(user_id=user_id, empresa_id=empresa_id).first():
        raise Exception("Usuário não tem acesso à empresa")

    # --------------- buscar empresa e token ---------------
    empresa: Empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        raise Exception("Empresa não encontrada")

    token = getattr(empresa, "nibo_api_token", None)
    if not token:
        raise Exception("Empresa não possui token Nibo salvo (nibo_api_token).")

    # --------------- carregar ativos locais ---------------
    ativos_db: List[Ativo] = db.query(Ativo).filter(Ativo.empresa_id == empresa_id).all()
    ativos_db_map = { _normalize_nibo_key(a.nibo_cost_center_id): a for a in ativos_db if a.nibo_cost_center_id is not None }
    ativo_sem_cc = db.query(Ativo).filter_by(empresa_id=empresa_id, nibo_cost_center_id=None).first()

    # --------------- buscar costcenters da Nibo ---------------
    try:
        costcenters_raw = await nibo_service.get_costcenters(token)
        if isinstance(costcenters_raw, dict):
            costcenters = costcenters_raw.get("items") or costcenters_raw.get("value") or []
        else:
            costcenters = costcenters_raw or []
    except Exception:
        try:
            costcenters = await fetch_all(token, nibo_service.get_costcenters)
        except Exception:
            costcenters = []

    nibo_centers = []
    for cc in costcenters:
        if isinstance(cc, dict):
            nibo_id = cc.get("costCenterId") or cc.get("id") or cc.get("costCenterID") or cc.get("centerId")
            nome = cc.get("description") or cc.get("name") or cc.get("title") or "Centro sem nome"
        else:
            nibo_id = cc
            nome = "Centro sem nome"
        nibo_centers.append({"id": nibo_id, "nome": nome, "raw": cc})

    # --------------- buscar movimentações ---------------
    try:
        receipts = await fetch_all_pages(nibo_service.get_receipts, token)
    except Exception:
        receipts = []
    try:
        payments = await fetch_all_pages(nibo_service.get_payments, token)
    except Exception:
        payments = []

    all_movs_raw = []
    for r in receipts:
        if r.get("isTransfer") is True or r.get("isTransfered") is True or r.get("is_transfer") is True:
            continue
        all_movs_raw.append(r)
    for p in payments:
        if p.get("isTransfer") is True or p.get("isTransfered") is True or p.get("is_transfer") is True:
            continue
        all_movs_raw.append(p)

    movs_by_cc: Dict[str, List[Dict[str, Any]]] = {}
    for item in all_movs_raw:
        cc_id = _extract_costcenter_id_from_item(item)
        key = _normalize_nibo_key(cc_id)
        movs_by_cc.setdefault(key, []).append(item)

    # --------------- processar cada centro ---------------
    novos_ativos = 0
    novas_movimentacoes = 0

    for center in nibo_centers:
        nibo_id = center["id"]
        nome = center["nome"]
        key = _normalize_nibo_key(nibo_id)

        ativo_existente = ativos_db_map.get(key)

        if ativo_existente:
            if not getattr(ativo_existente, "ativo", True):
                continue

            movs = movs_by_cc.get(key, [])

            for item in movs:
                nibo_tx_id = item.get("entryId") or item.get("id")
                if not nibo_tx_id:
                    continue

                existe = db.query(Movimentacao).filter(
                    Movimentacao.usuario_id == ativo_existente.usuario_id,
                    Movimentacao.nibo_transaction_id == nibo_tx_id
                ).first()
                if existe:
                    try:
                        if not db.query(MovimentacaoAtivo).filter_by(movimentacao_id=existe.id, ativo_id=ativo_existente.id).first():
                            db.add(MovimentacaoAtivo(
                                movimentacao_id=existe.id,
                                ativo_id=ativo_existente.id,
                                valor=_to_decimal(item.get("value") or item.get("amount") or 0) * ( -1 if item in payments else 1 ),
                                tipo="Recebimento" if (item.get("value") or item.get("amount") or 0) >= 0 else "Pagamento"
                            ))
                            db.flush()
                    except Exception:
                        db.rollback()
                    continue

                valor_raw = item.get("value") or item.get("amount") or 0
                valor = _to_decimal(valor_raw)
                tipo_mov = "Recebimento" if valor >= 0 else "Pagamento"

                mov = Movimentacao(
                    usuario_id=ativo_existente.usuario_id,
                    ativo_id=ativo_existente.id,
                    data_movimentacao=(item.get("date") or item.get("dueDate") or item.get("accrualDate") or None),
                    descricao=item.get("identifier") or item.get("description") or "",
                    valor=(valor if tipo_mov == "Recebimento" else -valor),
                    investimento=0,
                    rendimento_cdi=0,
                    saldo_cdi=0,
                    diferenca=0,
                    nibo_transaction_id=nibo_tx_id
                )
                try:
                    db.add(mov)
                    db.flush()

                    db.add(MovimentacaoAtivo(
                        movimentacao_id=mov.id,
                        ativo_id=ativo_existente.id,
                        valor=mov.valor,
                        tipo="Recebimento" if mov.valor >= 0 else "Pagamento"
                    ))
                    db.flush()

                    if mov.valor >= 0:
                        ativo_existente.receita = (ativo_existente.receita or Decimal("0")) + mov.valor
                    else:
                        ativo_existente.gastos = (ativo_existente.gastos or Decimal("0")) + mov.valor

                    ativo_existente.total = (ativo_existente.receita or Decimal("0")) + (ativo_existente.gastos or Decimal("0"))

                    db.add(ativo_existente)
                    db.flush()

                    novas_movimentacoes += 1
                except Exception:
                    db.rollback()
                    continue

            try:
                db.commit()
                db.refresh(ativo_existente)
            except Exception:
                try:
                    db.rollback()
                except:
                    pass
            continue

        # criar novo ativo
        try:
            novo_ativo = Ativo(
                usuario_id=user_id,
                empresa_id=empresa_id,
                nome=nome or "Centro sem nome",
                status=StatusAtivo.vazio,
                tipo=TipoAtivo.residencial,
                finalidade=FinalidadeAtivo.locacao_venda,
                grau_desmobilizacao=GrauDesmobilizacaoAtivo.moderado,
                potencial=PotencialAtivo.medio,
                percentual_participacao=100,
                valor_compra=Decimal("0"),
                gastos=Decimal("0"),
                receita=Decimal("0"),
                saldo_devedor=None,
                preco_venda=None,
                participacao_venda=100,
                nibo_cost_center_id=nibo_id,
                ativo=True
            )
            db.add(novo_ativo)
            db.flush()
            novos_ativos += 1

            ativos_db_map[key] = novo_ativo
        except IntegrityError:
            try:
                db.rollback()
            except:
                pass
            existing = db.query(Ativo).filter(Ativo.nibo_cost_center_id == nibo_id, Ativo.empresa_id == empresa_id).first()
            if existing:
                ativos_db_map[key] = existing
            else:
                continue
        except Exception:
            try:
                db.rollback()
            except:
                pass
            continue

        movs_for_new = movs_by_cc.get(key, [])
        for item in movs_for_new:
            nibo_tx_id = item.get("entryId") or item.get("id")
            if not nibo_tx_id:
                continue

            existe = db.query(Movimentacao).filter(Movimentacao.usuario_id == user_id, Movimentacao.nibo_transaction_id == nibo_tx_id).first()
            if existe:
                try:
                    if not db.query(MovimentacaoAtivo).filter_by(movimentacao_id=existe.id, ativo_id=novo_ativo.id).first():
                        db.add(MovimentacaoAtivo(
                            movimentacao_id=existe.id,
                            ativo_id=novo_ativo.id,
                            valor=_to_decimal(item.get("value") or item.get("amount") or 0),
                            tipo="Recebimento" if _to_decimal(item.get("value") or item.get("amount") or 0) >= 0 else "Pagamento"
                        ))
                        db.flush()
                except Exception:
                    db.rollback()
                continue

            valor = _to_decimal(item.get("value") or item.get("amount") or 0)
            mov = Movimentacao(
                usuario_id=user_id,
                ativo_id=novo_ativo.id,
                data_movimentacao=(item.get("date") or item.get("dueDate") or item.get("accrualDate") or None),
                descricao=item.get("identifier") or item.get("description") or "",
                valor=(valor if valor >= 0 else -valor),
                investimento=0,
                rendimento_cdi=0,
                saldo_cdi=0,
                diferenca=0,
                nibo_transaction_id=nibo_tx_id
            )
            try:
                db.add(mov)
                db.flush()

                db.add(MovimentacaoAtivo(
                    movimentacao_id=mov.id,
                    ativo_id=novo_ativo.id,
                    valor=mov.valor,
                    tipo="Recebimento" if mov.valor >= 0 else "Pagamento"
                ))
                db.flush()

                if mov.valor >= 0:
                    novo_ativo.receita = (novo_ativo.receita or Decimal("0")) + mov.valor
                else:
                    novo_ativo.gastos = (novo_ativo.gastos or Decimal("0")) + mov.valor

                novo_ativo.total = (novo_ativo.receita or Decimal("0")) + (novo_ativo.gastos or Decimal("0"))

                db.add(novo_ativo)
                db.flush()

                novas_movimentacoes += 1
            except Exception:
                db.rollback()
                continue

        try:
            db.commit()
            db.refresh(novo_ativo)
        except Exception:
            try:
                db.rollback()
            except:
                pass

    # --------------------------------------
    # CÁLCULO DO CDI — UMA ÚNICA VEZ (OPÇÃO A)
    # --------------------------------------
    try:
        recalcular_investimentos_cdi_empresa(db, empresa_id)
    except Exception as e:
        print("Erro ao recalcular investimentos CDI no refresh:", e)

    return {
        "status": "ok",
        "empresa_id": empresa_id,
        "novos_ativos": novos_ativos,
        "novas_movimentacoes": novas_movimentacoes,
    }
