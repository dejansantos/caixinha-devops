"""
Geração dos PDFs de relatório, usando fpdf2.
Separado das views para manter a lógica de "desenhar o PDF" isolada.
"""
from fpdf import FPDF


def _br(valor) -> str:
    """Formata Decimal como moeda BR: 1234.5 -> 'R$ 1.234,50'"""
    texto = f"{valor:,.2f}"
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def _seguro(texto: str) -> str:
    """Remove caracteres que a fonte padrão do PDF (latin-1) não suporta,
    evitando erro ao gerar o PDF com nomes/textos digitados livremente."""
    if texto is None:
        return ""
    return str(texto).encode("latin-1", "ignore").decode("latin-1")


class RelatorioPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, _seguro(self.titulo_relatorio), ln=True, align="C")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 6, _seguro(self.subtitulo_relatorio), ln=True, align="C")
        self.set_text_color(0, 0, 0)
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Página {self.page_no()}", align="C")


def gerar_pdf_resumo_geral(resumo: dict, cotistas: list, rifas: list = None) -> bytes:
    pdf = RelatorioPDF()
    pdf.titulo_relatorio = "Resumo Geral da Caixinha"
    pdf.subtitulo_relatorio = f"Ciclo: {resumo['ciclo'].nome} ({resumo['ciclo'].data_inicio:%d/%m/%Y} a {resumo['ciclo'].data_fim:%d/%m/%Y})"
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Totais do ciclo", ln=True)
    pdf.set_font("Helvetica", "", 10)

    linhas = [
        ("Capital de cotas pago", resumo["capital_cotas_pago"]),
        ("Capital de cotas pendente", resumo["capital_cotas_pendente"]),
        ("Lucro com rifas (líquido)", resumo["rifa_liquida_total"]),
        ("Juros recebidos (empréstimos quitados)", resumo["juros_recebidos"]),
        ("Rendimento de investimentos", resumo["rendimento_investimentos"]),
        ("Lucro total do ciclo", resumo["lucro_total"]),
        ("Valor emprestado ativo (ainda em aberto)", resumo["valor_emprestado_ativo"]),
        ("Saldo total da caixinha (capital + lucro)", resumo["saldo_total_caixinha"]),
        ("Cotistas ativos", str(resumo["qtd_cotistas_ativos"])),
    ]
    for label, valor in linhas:
        texto_valor = _br(valor) if not isinstance(valor, str) else valor
        pdf.cell(120, 7, label, border=0)
        pdf.cell(0, 7, texto_valor, ln=True, align="R")

    if rifas:
        pdf.ln(6)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "Rifas do ciclo (arrecadação x saída do prêmio)", ln=True)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(230, 230, 230)
        pdf.cell(50, 7, "Rifa", border=1, fill=True)
        pdf.cell(20, 7, "Mês", border=1, fill=True, align="C")
        pdf.cell(35, 7, "Arrecadação", border=1, fill=True, align="R")
        pdf.cell(30, 7, "Saída (prêmio)", border=1, fill=True, align="R")
        pdf.cell(35, 7, "Lucro líquido", border=1, fill=True, align="R")
        pdf.ln()
        pdf.set_font("Helvetica", "", 9)
        for linha in rifas:
            pdf.cell(50, 7, _seguro(linha["rifa"].titulo)[:28], border=1)
            pdf.cell(20, 7, f"{linha['rifa'].mes_referencia:%m/%Y}", border=1, align="C")
            pdf.cell(35, 7, _br(linha["arrecadacao_bruta"]), border=1, align="R")
            pdf.cell(30, 7, f"-{_br(linha['custo_premio'])}", border=1, align="R")
            pdf.cell(35, 7, _br(linha["lucro_liquido"]), border=1, align="R")
            pdf.ln()

    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Por cotista (cotas do ciclo)", ln=True)

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(80, 7, "Cotista", border=1, fill=True)
    pdf.cell(25, 7, "Qtd cotas", border=1, fill=True, align="C")
    pdf.cell(40, 7, "Total pago", border=1, fill=True, align="R")
    pdf.cell(40, 7, "Pendente", border=1, fill=True, align="R")
    pdf.ln()

    pdf.set_font("Helvetica", "", 9)
    for linha in cotistas:
        pdf.cell(80, 7, _seguro(linha["cotista"].nome)[:45], border=1)
        pdf.cell(25, 7, str(linha["qtd_cotas"]), border=1, align="C")
        pdf.cell(40, 7, _br(linha["total_pago"]), border=1, align="R")
        pdf.cell(40, 7, _br(linha["total_pendente"]), border=1, align="R")
        pdf.ln()

    return bytes(pdf.output())


def gerar_pdf_extrato_cotista(dados: dict) -> bytes:
    cotista = dados["cotista"]
    ciclo = dados["ciclo"]

    pdf = RelatorioPDF()
    pdf.titulo_relatorio = f"Extrato - {cotista.nome}"
    pdf.subtitulo_relatorio = f"Ciclo: {ciclo.nome} ({ciclo.data_inicio:%d/%m/%Y} a {ciclo.data_fim:%d/%m/%Y})"
    pdf.add_page()

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 7, f"Quantidade de cotas: {cotista.qtd_cotas}", ln=True)
    pdf.cell(0, 7, f"Total pago no ciclo: {_br(dados['total_pago'])}", ln=True)
    pdf.cell(0, 7, f"Total pendente no ciclo: {_br(dados['total_pendente'])}", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Cotas mensais", ln=True)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(50, 7, "Mês", border=1, fill=True)
    pdf.cell(40, 7, "Valor", border=1, fill=True, align="R")
    pdf.cell(30, 7, "Pago?", border=1, fill=True, align="C")
    pdf.cell(50, 7, "Data pagamento", border=1, fill=True, align="C")
    pdf.ln()
    pdf.set_font("Helvetica", "", 9)
    for cota in dados["cotas"]:
        pdf.cell(50, 7, f"{cota.mes_referencia:%m/%Y}", border=1)
        pdf.cell(40, 7, _br(cota.valor), border=1, align="R")
        pdf.cell(30, 7, "Sim" if cota.pago else "Não", border=1, align="C")
        data_pg = f"{cota.data_pagamento:%d/%m/%Y}" if cota.data_pagamento else "-"
        pdf.cell(50, 7, data_pg, border=1, align="C")
        pdf.ln()

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(180, 0, 0)
    pdf.cell(0, 8, f"TOTAL DEVIDO HOJE: {_br(dados['total_devido_geral'])}", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 6, f"  Cotas pendentes: {_br(dados['total_pendente'])}", ln=True)
    pdf.cell(0, 6, f"  Empréstimos pendentes (com multa): {_br(dados['total_devido_emprestimos'])}", ln=True)
    pdf.cell(0, 6, f"  Rifas pendentes: {_br(dados['total_devido_rifas'])}", ln=True)

    if dados["emprestimos_detalhados"]:
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "Empréstimos", ln=True)
        for item in dados["emprestimos_detalhados"]:
            emp = item["emprestimo"]
            pdf.set_font("Helvetica", "B", 9)
            situacao = "ATRASADO" if item["atrasado"] else emp.get_status_display()
            if item["atrasado"]:
                pdf.set_text_color(180, 0, 0)
            pdf.cell(
                0, 6,
                f"{emp.data_emprestimo:%d/%m/%Y} - Principal {_br(emp.valor_principal)} - "
                f"Juros {emp.taxa_juros}% - Total {_br(emp.valor_total_com_juros)} - {situacao}",
                ln=True,
            )
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Helvetica", "", 8)
            texto_parcelas = f"   Parcelas: {item['qtd_pagas']}/{item['qtd_parcelas']} pagas"
            if item["qtd_atrasadas"]:
                texto_parcelas += f" - {item['qtd_atrasadas']} atrasada(s)"
            texto_parcelas += f" - Pendente: {_br(item['valor_pendente'])}"
            pdf.cell(0, 5, texto_parcelas, ln=True)
            pdf.ln(1)

    if dados["rifas_pagamentos"].exists():
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "Rifas mensais", ln=True)
        pdf.set_font("Helvetica", "", 9)
        for pr in dados["rifas_pagamentos"]:
            status = "Pago" if pr.pago else "Pendente"
            pdf.cell(0, 7, f"{_seguro(pr.rifa.titulo)} - {_br(pr.valor)} - {status}", ln=True)

    if dados["rateio"]:
        r = dados["rateio"]
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "Rateio final do ciclo", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 7, f"Capital das cotas devolvido: {_br(r.capital_cotas)}", ln=True)
        pdf.cell(0, 7, f"Lucro distribuído: {_br(r.lucro_distribuido)}", ln=True)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 7, f"Saldo final a receber: {_br(r.saldo_final)}", ln=True)

    return bytes(pdf.output())
