from django.contrib import admin as django_admin
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404

from .models import Cotista
from .reports import resumo_geral, resumo_por_cotista, extrato_cotista, rifas_detalhado, get_ciclo_padrao


@staff_member_required
def dashboard_view(request):
    ciclo = get_ciclo_padrao()

    # each_context traz tudo que o layout do admin/Jazzmin precisa:
    # menu lateral, cabeçalho, permissões, cores — sem isso a página
    # renderiza "crua", sem o visual do resto do sistema.
    contexto = django_admin.site.each_context(request)

    if not ciclo:
        contexto["sem_ciclo"] = True
        return render(request, "core/dashboard.html", contexto)

    contexto.update({
        "title": "Relatório",
        "resumo": resumo_geral(ciclo),
        "cotistas": resumo_por_cotista(ciclo),
        "rifas": rifas_detalhado(ciclo),
        "ciclo": ciclo,
    })
    return render(request, "core/dashboard.html", contexto)


@staff_member_required
def extrato_cotista_html(request, cotista_id):
    cotista = get_object_or_404(Cotista, pk=cotista_id)
    ciclo = get_ciclo_padrao()
    if not ciclo:
        raise Http404("Nenhum ciclo cadastrado.")

    contexto = django_admin.site.each_context(request)
    contexto["title"] = f"Extrato - {cotista.nome}"
    contexto.update(extrato_cotista(cotista, ciclo))
    return render(request, "core/extrato_cotista.html", contexto)


@staff_member_required
def relatorio_geral_pdf(request):
    from .pdf_reports import gerar_pdf_resumo_geral

    ciclo = get_ciclo_padrao()
    if not ciclo:
        raise Http404("Nenhum ciclo cadastrado.")

    resumo = resumo_geral(ciclo)
    cotistas = resumo_por_cotista(ciclo)
    rifas = rifas_detalhado(ciclo)
    pdf_bytes = gerar_pdf_resumo_geral(resumo, cotistas, rifas)

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="resumo_geral_{ciclo.nome}.pdf"'
    return response


@staff_member_required
def extrato_cotista_pdf(request, cotista_id):
    from .pdf_reports import gerar_pdf_extrato_cotista

    cotista = get_object_or_404(Cotista, pk=cotista_id)
    ciclo = get_ciclo_padrao()
    if not ciclo:
        raise Http404("Nenhum ciclo cadastrado.")

    dados = extrato_cotista(cotista, ciclo)
    pdf_bytes = gerar_pdf_extrato_cotista(dados)

    nome_arquivo = f"extrato_{cotista.nome.replace(' ', '_')}_{ciclo.nome}.pdf"
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{nome_arquivo}"'
    return response
