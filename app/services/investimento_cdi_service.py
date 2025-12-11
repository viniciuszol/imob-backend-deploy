from sqlalchemy.orm import Session
from datetime import date
from dateutil.relativedelta import relativedelta

from app.models import Ativo, Movimentacao, InvestimentoCDI, CDI


def gerar_investimento_cdi_para_ativo(db: Session, ativo_id: int):
    """
    Gera a série de investimento_cdi para UM ativo, do primeiro mês de movimentação
    até o mês atual, sem pular nenhum mês.
    NÃO apaga nada antes — isso é responsabilidade da função de nível empresa.
    """
    ativo = db.query(Ativo).filter(Ativo.id == ativo_id).first()
    if not ativo:
        return

    # valor base vem do ativo
    valor_base = ativo.valor_compra or 0

    # pegar movimentação mais antiga
    mov = (
        db.query(Movimentacao)
        .filter(Movimentacao.ativo_id == ativo_id)
        .order_by(Movimentacao.data_movimentacao.asc())
        .first()
    )

    if not mov:
        # sem movimentação, sem CDI
        return

    # mês inicial (1º dia do mês da primeira movimentação)
    current = mov.data_movimentacao.replace(day=1)

    # mês atual (1º dia do mês corrente)
    limite = date.today().replace(day=1)

    acumulado = 0.0

    while current <= limite:
        cdi = db.query(CDI).filter(CDI.data == current).first()

        if cdi:
            # cdi.cdi_am já é o fator decimal (ex: 0.0076 = 0,76% ao mês)
            rendimento_mes = float(valor_base) * float(cdi.cdi_am)
            cdi_mes = float(cdi.cdi_am)
        else:
            rendimento_mes = 0.0
            cdi_mes = 0.0

        acumulado += rendimento_mes

        # verifica se já existe registro para esse mês
        registro = (
            db.query(InvestimentoCDI)
            .filter(
                InvestimentoCDI.ativo_id == ativo_id,
                InvestimentoCDI.data == current,
            )
            .first()
        )

        if not registro:
            registro = InvestimentoCDI(
                ativo_id=ativo_id,
                data=current,
            )
            db.add(registro)

        registro.ano = current.year
        registro.mes = current.month
        registro.valor_compra_ativo = valor_base
        registro.cdi_mes = cdi_mes
        registro.rendimento_cdi_mes = rendimento_mes
        registro.rendimento_cdi_acumulado = acumulado
        registro.diferenca_rendimento = 0 - rendimento_mes

        current += relativedelta(months=1)


def recalcular_investimentos_cdi_empresa(db: Session, empresa_id: int):
    """
    Estratégia A:
      - Apaga TODOS os registros de investimento_cdi dos ativos dessa empresa
      - Recalcula do zero para cada ativo da empresa
    """
    # pega todos os ativos da empresa
    ativos_ids = (
        db.query(Ativo.id)
        .filter(Ativo.empresa_id == empresa_id)
        .all()
    )
    ativos_ids = [row[0] for row in ativos_ids]

    if not ativos_ids:
        return

    # apaga todos os registros de investimento_cdi desses ativos
    db.query(InvestimentoCDI).filter(
        InvestimentoCDI.ativo_id.in_(ativos_ids)
    ).delete(synchronize_session=False)
    db.flush()

    # recalcula para cada ativo
    for ativo_id in ativos_ids:
        gerar_investimento_cdi_para_ativo(db, ativo_id)

    db.commit()
