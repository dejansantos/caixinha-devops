"""
Sistema de Gestão de Caixinha
Modelo de dados baseado nas regras de negócio definidas:

- Ciclo custom: 1º dezembro -> 30 novembro do ano seguinte
- Rifas mensais: apenas fevereiro a outubro
- Juros simples, taxa definida por empréstimo (não fixa por cotista)
- Multa de atraso: gerada automaticamente, mas editável
- No fechamento do ciclo:
    * Cotas aportadas voltam integralmente para cada cotista (principal)
    * Lucro do ciclo (rifa líquida + juros + rendimento investimento)
      é rateado proporcionalmente à quantidade de cotas de cada cotista
- Log de auditoria em todas as tabelas sensíveis
"""

from decimal import Decimal
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


# ---------------------------------------------------------------------------
# Ciclo Anual (dezembro -> novembro)
# ---------------------------------------------------------------------------
class CicloAnual(models.Model):
    """Representa um ciclo da caixinha. Ex: Ciclo 2026/2027 = 01/12/2026 a 30/11/2027"""

    ABERTO = "aberto"
    FECHADO = "fechado"
    STATUS_CHOICES = [(ABERTO, "Aberto"), (FECHADO, "Fechado")]

    nome = models.CharField(max_length=50, help_text="Ex: Ciclo 2026/2027")
    data_inicio = models.DateField(help_text="Sempre 1º de dezembro")
    data_fim = models.DateField(help_text="Sempre 30 de novembro do ano seguinte")
    valor_unitario_cota = models.DecimalField(
        max_digits=8, decimal_places=2, default=Decimal("50.00"),
        help_text="Valor de 1 cota nesse ciclo (ex: R$50,00). Usado para calcular o valor mensal automaticamente."
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=ABERTO)
    lucro_total_apurado = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00"),
        help_text="Preenchido automaticamente ao fechar o ciclo"
    )
    data_fechamento = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-data_inicio"]

    def __str__(self):
        return self.nome

    def clean(self):
        if self.data_inicio and self.data_inicio.month != 12:
            raise ValidationError("Ciclo deve sempre iniciar em dezembro.")
        if self.data_fim and self.data_fim.month != 11:
            raise ValidationError("Ciclo deve sempre terminar em novembro.")

    @property
    def total_cotas_aportadas(self):
        return self.cotas.aggregate(total=models.Sum("valor"))["total"] or Decimal("0.00")

    def calcular_lucro_ciclo(self):
        """Soma rifa líquida + juros de empréstimos + rendimento de investimentos do ciclo."""
        origens_lucro = [Movimentacao.ORIGEM_RIFA, Movimentacao.ORIGEM_JUROS, Movimentacao.ORIGEM_INVESTIMENTO]
        total = self.movimentacoes.filter(
            tipo=Movimentacao.ENTRADA, origem__in=origens_lucro
        ).aggregate(total=models.Sum("valor"))["total"] or Decimal("0.00")
        return total


# ---------------------------------------------------------------------------
# Cotista
# ---------------------------------------------------------------------------
class Cotista(models.Model):
    ATIVO = "ativo"
    INATIVO = "inativo"
    STATUS_CHOICES = [(ATIVO, "Ativo"), (INATIVO, "Inativo")]

    nome = models.CharField(max_length=120)
    telefone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    qtd_cotas = models.PositiveIntegerField(default=1, help_text="Usado para ratear lucro/prejuízo")
    taxa_juros_padrao = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00"),
        help_text="Taxa sugerida (%) ao criar empréstimo — pode ser sobrescrita"
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=ATIVO)
    data_entrada = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome

    def saldo_cotas_no_ciclo(self, ciclo: CicloAnual) -> Decimal:
        return self.cotas.filter(ciclo=ciclo).aggregate(
            total=models.Sum("valor"))["total"] or Decimal("0.00")


# ---------------------------------------------------------------------------
# Cota (aporte mensal do cotista)
# ---------------------------------------------------------------------------
class Cota(models.Model):
    cotista = models.ForeignKey(Cotista, on_delete=models.PROTECT, related_name="cotas")
    ciclo = models.ForeignKey(CicloAnual, on_delete=models.PROTECT, related_name="cotas")
    mes_referencia = models.DateField(help_text="Mês/ano de referência do aporte")
    valor = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True,
        help_text="Deixe em branco para calcular automaticamente (qtd_cotas x valor da cota no ciclo). "
                   "Preencha manualmente só se esse mês for diferente do padrão."
    )
    data_pagamento = models.DateField(null=True, blank=True)
    pago = models.BooleanField(default=False)

    class Meta:
        ordering = ["-mes_referencia"]
        unique_together = ["cotista", "ciclo", "mes_referencia"]

    def __str__(self):
        return f"{self.cotista} - {self.mes_referencia:%m/%Y} - R${self.valor}"

    def save(self, *args, **kwargs):
        if self.valor is None:
            self.valor = self.cotista.qtd_cotas * self.ciclo.valor_unitario_cota
        super().save(*args, **kwargs)


# ---------------------------------------------------------------------------
# Empréstimo + Parcelas
# ---------------------------------------------------------------------------
class Emprestimo(models.Model):
    ATIVO = "ativo"
    QUITADO = "quitado"
    ATRASADO = "atrasado"
    RENEGOCIADO = "renegociado"
    STATUS_CHOICES = [
        (ATIVO, "Ativo"), (QUITADO, "Quitado"), (ATRASADO, "Atrasado"),
        (RENEGOCIADO, "Renegociado (consolidado em outro empréstimo)"),
    ]

    cotista = models.ForeignKey(Cotista, on_delete=models.PROTECT, related_name="emprestimos")
    ciclo = models.ForeignKey(CicloAnual, on_delete=models.PROTECT, related_name="emprestimos")
    valor_principal = models.DecimalField(max_digits=10, decimal_places=2)
    taxa_juros = models.DecimalField(
        max_digits=5, decimal_places=2,
        help_text="% de juros SIMPLES aplicado — definido por empréstimo, pode variar por situação"
    )
    qtd_parcelas = models.PositiveIntegerField(default=1)
    data_emprestimo = models.DateField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default=ATIVO)
    observacoes = models.TextField(blank=True)

    class Meta:
        ordering = ["-data_emprestimo"]

    def __str__(self):
        return f"Empréstimo {self.cotista} - R${self.valor_principal} ({self.taxa_juros}%)"

    @property
    def valor_total_com_juros(self) -> Decimal:
        """Juros simples MENSAL: J = C x i x n (principal x taxa% x quantidade de parcelas/meses)"""
        juros = self.valor_principal * (self.taxa_juros / Decimal("100")) * self.qtd_parcelas
        return self.valor_principal + juros

    @property
    def valor_parcela(self) -> Decimal:
        return round(self.valor_total_com_juros / self.qtd_parcelas, 2)

    def gerar_parcelas(self):
        """Cria as parcelas automaticamente a partir da data do empréstimo."""
        from dateutil.relativedelta import relativedelta
        if self.parcelas.exists():
            return
        for i in range(1, self.qtd_parcelas + 1):
            Parcela.objects.create(
                emprestimo=self,
                numero=i,
                valor=self.valor_parcela,
                vencimento=self.data_emprestimo + relativedelta(months=i),
            )


class Parcela(models.Model):
    emprestimo = models.ForeignKey(Emprestimo, on_delete=models.CASCADE, related_name="parcelas")
    numero = models.PositiveIntegerField()
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    vencimento = models.DateField()
    pago = models.BooleanField(default=False)
    data_pagamento = models.DateField(null=True, blank=True)
    multa_valor = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"),
        help_text="Gerada automaticamente em atraso, mas editável manualmente"
    )
    multa_editada_manualmente = models.BooleanField(default=False)

    class Meta:
        ordering = ["numero"]
        unique_together = ["emprestimo", "numero"]

    def __str__(self):
        return f"Parcela {self.numero}/{self.emprestimo.qtd_parcelas} - {self.emprestimo.cotista}"

    def calcular_multa_automatica(self, percentual_multa=Decimal("2.00")):
        """Chamado por job diário: se vencida e não paga e não editada manualmente, aplica multa sugerida."""
        from datetime import date
        if not self.pago and self.vencimento < date.today() and not self.multa_editada_manualmente:
            self.multa_valor = round(self.valor * (percentual_multa / Decimal("100")), 2)
            self.save(update_fields=["multa_valor"])


# ---------------------------------------------------------------------------
# Rifa mensal (fevereiro a outubro apenas)
# ---------------------------------------------------------------------------
class RifaMensal(models.Model):
    MESES_PERMITIDOS = range(2, 11)  # fevereiro(2) a outubro(10)

    ciclo = models.ForeignKey(CicloAnual, on_delete=models.PROTECT, related_name="rifas")
    titulo = models.CharField(max_length=120)
    mes_referencia = models.DateField()
    valor_bilhete = models.DecimalField(max_digits=8, decimal_places=2)
    qtd_bilhetes_vendidos = models.PositiveIntegerField(
        default=0,
        help_text="Legado/manual. Se estiver usando PagamentoRifa (recomendado), pode deixar 0 — "
                   "a arrecadação passa a ser calculada automaticamente pelos pagamentos registrados."
    )
    custo_premio = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    data_sorteio = models.DateField()

    class Meta:
        ordering = ["mes_referencia"]

    def __str__(self):
        return f"{self.titulo} ({self.mes_referencia:%m/%Y})"

    def clean(self):
        if self.mes_referencia and self.mes_referencia.month not in self.MESES_PERMITIDOS:
            raise ValidationError("Rifas mensais só podem ocorrer entre fevereiro e outubro.")

    @property
    def arrecadacao_bruta(self) -> Decimal:
        """Calculada a partir dos pagamentos individuais confirmados (PagamentoRifa)."""
        if self.pagamentos.exists():
            total = self.pagamentos.filter(pago=True).aggregate(
                total=models.Sum("valor"))["total"] or Decimal("0.00")
            return total
        # fallback pro modo antigo (campo manual), caso não esteja usando PagamentoRifa
        return self.valor_bilhete * self.qtd_bilhetes_vendidos

    @property
    def arrecadacao_liquida(self) -> Decimal:
        return self.arrecadacao_bruta - self.custo_premio

    @property
    def total_pendentes(self) -> int:
        return self.pagamentos.filter(pago=False).count()


class PagamentoRifa(models.Model):
    """Participação/pagamento de um cotista numa rifa mensal específica.
    Cada cotista compra sempre 1 bilhete/mês (valor fixo = valor_bilhete da rifa)."""

    rifa = models.ForeignKey(RifaMensal, on_delete=models.CASCADE, related_name="pagamentos")
    cotista = models.ForeignKey(Cotista, on_delete=models.PROTECT, related_name="pagamentos_rifa")
    valor = models.DecimalField(
        max_digits=8, decimal_places=2, blank=True, null=True,
        help_text="Deixe em branco para usar o valor_bilhete da rifa automaticamente."
    )
    pago = models.BooleanField(default=False)
    data_pagamento = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ["rifa", "cotista"]
        ordering = ["cotista__nome"]

    def __str__(self):
        return f"{self.cotista} - {self.rifa} - {'Pago' if self.pago else 'Pendente'}"

    def save(self, *args, **kwargs):
        if self.valor is None:
            self.valor = self.rifa.valor_bilhete
        super().save(*args, **kwargs)


# ---------------------------------------------------------------------------
# Investimento
# ---------------------------------------------------------------------------
class Investimento(models.Model):
    ciclo = models.ForeignKey(CicloAnual, on_delete=models.PROTECT, related_name="investimentos")
    descricao = models.CharField(max_length=120)
    valor_aplicado = models.DecimalField(max_digits=12, decimal_places=2)
    rendimento_apurado = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    data_aplicacao = models.DateField()
    data_resgate = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.descricao} - R${self.valor_aplicado}"


# ---------------------------------------------------------------------------
# Movimentação (livro-caixa único — fonte de verdade pro extrato/resumo)
# ---------------------------------------------------------------------------
class Movimentacao(models.Model):
    ENTRADA = "entrada"
    SAIDA = "saida"
    TIPO_CHOICES = [(ENTRADA, "Entrada"), (SAIDA, "Saída")]

    ORIGEM_COTA = "cota"
    ORIGEM_RIFA = "rifa"
    ORIGEM_JUROS = "juros_emprestimo"
    ORIGEM_INVESTIMENTO = "rendimento_investimento"
    ORIGEM_SAQUE = "saque_ciclo"
    ORIGEM_OUTRO = "outro"
    ORIGEM_CHOICES = [
        (ORIGEM_COTA, "Cota de cotista"),
        (ORIGEM_RIFA, "Rifa"),
        (ORIGEM_JUROS, "Juros de empréstimo"),
        (ORIGEM_INVESTIMENTO, "Rendimento de investimento"),
        (ORIGEM_SAQUE, "Saque de fechamento de ciclo"),
        (ORIGEM_OUTRO, "Outro"),
    ]

    ciclo = models.ForeignKey(CicloAnual, on_delete=models.PROTECT, related_name="movimentacoes")
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    origem = models.CharField(max_length=30, choices=ORIGEM_CHOICES)
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    data = models.DateField()
    descricao = models.CharField(max_length=200, blank=True)
    cotista_relacionado = models.ForeignKey(
        Cotista, on_delete=models.SET_NULL, null=True, blank=True, related_name="movimentacoes"
    )

    class Meta:
        ordering = ["-data"]

    def __str__(self):
        sinal = "+" if self.tipo == self.ENTRADA else "-"
        return f"{sinal}R${self.valor} ({self.get_origem_display()}) - {self.data}"


# ---------------------------------------------------------------------------
# Rateio (gerado no fechamento do ciclo)
# ---------------------------------------------------------------------------
class Rateio(models.Model):
    ciclo = models.ForeignKey(CicloAnual, on_delete=models.PROTECT, related_name="rateios")
    cotista = models.ForeignKey(Cotista, on_delete=models.PROTECT, related_name="rateios")
    capital_cotas = models.DecimalField(max_digits=12, decimal_places=2)
    lucro_distribuido = models.DecimalField(max_digits=12, decimal_places=2)
    saldo_final = models.DecimalField(max_digits=12, decimal_places=2)
    data_calculo = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["ciclo", "cotista"]

    def __str__(self):
        return f"Rateio {self.cotista} - Ciclo {self.ciclo} - R${self.saldo_final}"

    @staticmethod
    def gerar_para_ciclo(ciclo: CicloAnual):
        """
        Fecha o ciclo:
        - Capital das cotas volta integralmente para cada cotista
        - Lucro do ciclo é rateado proporcionalmente à qtd_cotas de cada cotista
        """
        lucro_total = ciclo.calcular_lucro_ciclo()
        cotistas = Cotista.objects.filter(status=Cotista.ATIVO)
        total_cotas_sistema = sum(c.qtd_cotas for c in cotistas) or 1

        rateios_criados = []
        for cotista in cotistas:
            capital = cotista.saldo_cotas_no_ciclo(ciclo)
            proporcao = Decimal(cotista.qtd_cotas) / Decimal(total_cotas_sistema)
            lucro_cotista = round(lucro_total * proporcao, 2)
            rateio, _ = Rateio.objects.update_or_create(
                ciclo=ciclo, cotista=cotista,
                defaults={
                    "capital_cotas": capital,
                    "lucro_distribuido": lucro_cotista,
                    "saldo_final": capital + lucro_cotista,
                }
            )
            rateios_criados.append(rateio)

        ciclo.lucro_total_apurado = lucro_total
        ciclo.status = CicloAnual.FECHADO
        from django.utils import timezone
        ciclo.data_fechamento = timezone.now()
        ciclo.save()
        return rateios_criados


# ---------------------------------------------------------------------------
# Log de Auditoria
# ---------------------------------------------------------------------------
class LogAuditoria(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    acao = models.CharField(max_length=20)  # criar, editar, excluir
    tabela = models.CharField(max_length=50)
    registro_id = models.PositiveIntegerField()
    valores_antes = models.JSONField(null=True, blank=True)
    valores_depois = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.usuario} {self.acao} {self.tabela}#{self.registro_id} em {self.timestamp:%d/%m/%Y %H:%M}"
