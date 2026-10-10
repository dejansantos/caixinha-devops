"""
Funções de cálculo dos relatórios (resumo geral e extrato por cotista).
Centralizadas aqui para serem reutilizadas tanto pela tela (dashboard)
quanto pela geração de PDF — evita duplicar a lógica em dois lugares.
"""
from decimal import Decimal

from django.db.models import Sum

from .models import (
    CicloAnual, Cotista, Cota, Emprestimo, RifaMensal, PagamentoRifa,
    Investimento, Rateio,
)


def resumo_geral(ciclo: CicloAnual) -> dict:
    """Números consolidados da caixinha inteira para um ciclo."""
    capital_cotas = Cota.objects.filter(ciclo=ciclo, pago=True).aggregate(
        t=Sum("valor"))["t"] or Decimal("0.00")
    capital_pendente = Cota.objects.filter(ciclo=ciclo, pago=False).aggregate(
        t=Sum("valor"))["t"] or Decimal("0.00")

    rifas = RifaMensal.objects.filter(ciclo=ciclo)
    rifa_liquida_total = sum((r.arrecadacao_liquida for r in rifas), Decimal("0.00"))

    emprestimos_quitados = Emprestimo.objects.filter(ciclo=ciclo, status=Emprestimo.QUITADO)
    juros_recebidos = sum(
        (e.valor_total_com_juros - e.valor_principal for e in emprestimos_quitados), Decimal("0.00")
    )
    emprestimos_ativos = Emprestimo.objects.filter(ciclo=ciclo, status=Emprestimo.ATIVO)
    valor_emprestado_ativo = emprestimos_ativos.aggregate(t=Sum("valor_principal"))["t"] or Decimal("0.00")

    rendimento_investimentos = Investimento.objects.filter(ciclo=ciclo).aggregate(
        t=Sum("rendimento_apurado"))["t"] or Decimal("0.00")

    lucro_total = rifa_liquida_total + juros_recebidos + rendimento_investimentos

    return {
        "ciclo": ciclo,
        "capital_cotas_pago": capital_cotas,
        "capital_cotas_pendente": capital_pendente,
        "rifa_liquida_total": rifa_liquida_total,
        "juros_recebidos": juros_recebidos,
        "rendimento_investimentos": rendimento_investimentos,
        "lucro_total": lucro_total,
        "valor_emprestado_ativo": valor_emprestado_ativo,
        "saldo_total_caixinha": capital_cotas + lucro_total,
        "qtd_cotistas_ativos": Cotista.objects.filter(status=Cotista.ATIVO).count(),
    }


def resumo_por_cotista(ciclo: CicloAnual) -> list:
    """Lista resumida (uma linha por cotista) para a tabela do dashboard."""
    linhas = []
    for cotista in Cotista.objects.filter(status=Cotista.ATIVO).order_by("nome"):
        pago = Cota.objects.filter(cotista=cotista, ciclo=ciclo, pago=True).aggregate(
            t=Sum("valor"))["t"] or Decimal("0.00")
        pendente = Cota.objects.filter(cotista=cotista, ciclo=ciclo, pago=False).aggregate(
            t=Sum("valor"))["t"] or Decimal("0.00")
        linhas.append({
            "cotista": cotista,
            "qtd_cotas": cotista.qtd_cotas,
            "total_pago": pago,
            "total_pendente": pendente,
        })
    return linhas


def extrato_cotista(cotista: Cotista, ciclo: CicloAnual) -> dict:
    """Extrato completo de um cotista específico dentro de um ciclo."""
    from datetime import date

    cotas = Cota.objects.filter(cotista=cotista, ciclo=ciclo).order_by("mes_referencia")
    total_pago = cotas.filter(pago=True).aggregate(t=Sum("valor"))["t"] or Decimal("0.00")
    total_pendente = cotas.filter(pago=False).aggregate(t=Sum("valor"))["t"] or Decimal("0.00")

    hoje = date.today()
    emprestimos_detalhados = []
    total_devido_emprestimos = Decimal("0.00")
    for emp in Emprestimo.objects.filter(cotista=cotista, ciclo=ciclo).order_by("-data_emprestimo"):
        parcelas = list(emp.parcelas.order_by("numero"))
        parcelas_pendentes = [p for p in parcelas if not p.pago]
        renegociado = emp.status == Emprestimo.RENEGOCIADO
        parcelas_atrasadas = [] if renegociado else [p for p in parcelas_pendentes if p.vencimento < hoje]
        valor_pendente = sum((p.valor + p.multa_valor for p in parcelas_pendentes), Decimal("0.00"))
        if not renegociado:
            total_devido_emprestimos += valor_pendente
        emprestimos_detalhados.append({
            "emprestimo": emp,
            "parcelas": parcelas,
            "qtd_parcelas": len(parcelas),
            "qtd_pagas": len(parcelas) - len(parcelas_pendentes),
            "qtd_pendentes": len(parcelas_pendentes),
            "qtd_atrasadas": len(parcelas_atrasadas),
            "atrasado": len(parcelas_atrasadas) > 0,
            "renegociado": renegociado,
            "valor_pendente": valor_pendente,
        })

    rifas_pagamentos = PagamentoRifa.objects.filter(cotista=cotista, rifa__ciclo=ciclo).order_by(
        "rifa__mes_referencia")
    total_devido_rifas = rifas_pagamentos.filter(pago=False).aggregate(
        t=Sum("valor"))["t"] or Decimal("0.00")

    total_devido_geral = total_pendente + total_devido_emprestimos + total_devido_rifas

    rateio = Rateio.objects.filter(cotista=cotista, ciclo=ciclo).first()

    return {
        "cotista": cotista,
        "ciclo": ciclo,
        "cotas": cotas,
        "total_pago": total_pago,
        "total_pendente": total_pendente,
        "emprestimos_detalhados": emprestimos_detalhados,
        "total_devido_emprestimos": total_devido_emprestimos,
        "rifas_pagamentos": rifas_pagamentos,
        "total_devido_rifas": total_devido_rifas,
        "total_devido_geral": total_devido_geral,
        "rateio": rateio,
    }


def rifas_detalhado(ciclo: CicloAnual) -> list:
    """Detalhe mês a mês de cada rifa: arrecadação bruta, custo do prêmio (saída) e lucro líquido."""
    linhas = []
    for rifa in RifaMensal.objects.filter(ciclo=ciclo).order_by("mes_referencia"):
        linhas.append({
            "rifa": rifa,
            "arrecadacao_bruta": rifa.arrecadacao_bruta,
            "custo_premio": rifa.custo_premio,
            "lucro_liquido": rifa.arrecadacao_liquida,
        })
    return linhas


def get_ciclo_padrao():
    """Ciclo aberto, ou o mais recente se nenhum estiver aberto."""
    return (
        CicloAnual.objects.filter(status=CicloAnual.ABERTO).first()
        or CicloAnual.objects.order_by("-data_inicio").first()
    )
