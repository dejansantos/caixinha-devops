from django.contrib import admin, messages
from django.utils import timezone
from .models import (
    CicloAnual, Cotista, Cota, Emprestimo, Parcela,
    RifaMensal, PagamentoRifa, Investimento, Movimentacao, Rateio, LogAuditoria,
)


@admin.register(CicloAnual)
class CicloAnualAdmin(admin.ModelAdmin):
    list_display = ("nome", "data_inicio", "data_fim", "valor_unitario_cota", "status", "lucro_total_apurado")
    list_filter = ("status",)


@admin.register(Cota)
class CotaAdmin(admin.ModelAdmin):
    list_display = ("cotista", "ciclo", "mes_referencia", "valor", "pago", "data_pagamento")
    list_filter = ("ciclo", "pago", "mes_referencia")
    search_fields = ("cotista__nome",)
    actions = ["gerar_cota_do_mes_todos_cotistas"]

    @admin.action(description="Gerar cota do mês atual para todos os cotistas ativos")
    def gerar_cota_do_mes_todos_cotistas(self, request, queryset):
        ciclo = CicloAnual.objects.filter(status=CicloAnual.ABERTO).first()
        if not ciclo:
            self.message_user(request, "Nenhum ciclo aberto encontrado.", level=messages.ERROR)
            return
        hoje = timezone.now().date()
        mes_ref = hoje.replace(day=1)
        criadas, existentes = 0, 0
        for cotista in Cotista.objects.filter(status=Cotista.ATIVO):
            _, foi_criada = Cota.objects.get_or_create(
                cotista=cotista, ciclo=ciclo, mes_referencia=mes_ref,
            )
            criadas += 1 if foi_criada else 0
            existentes += 0 if foi_criada else 1
        self.message_user(
            request,
            f"{criadas} cota(s) criada(s) para {mes_ref:%m/%Y}. {existentes} já existiam.",
            level=messages.SUCCESS,
        )


class CotaInline(admin.TabularInline):
    model = Cota
    extra = 0
    fields = ("mes_referencia", "valor", "pago", "data_pagamento")
    ordering = ("mes_referencia",)


class PagamentoRifaCotistaInline(admin.TabularInline):
    model = PagamentoRifa
    extra = 0
    fields = ("rifa", "valor", "pago", "data_pagamento")


@admin.register(Cotista)
class CotistaAdmin(admin.ModelAdmin):
    list_display = ("nome", "qtd_cotas", "taxa_juros_padrao", "status", "data_entrada")
    list_filter = ("status",)
    search_fields = ("nome", "email", "telefone")
    inlines = [CotaInline, PagamentoRifaCotistaInline]


class ParcelaInline(admin.TabularInline):
    model = Parcela
    extra = 0
    can_delete = False

    def get_readonly_fields(self, request, obj=None):
        # Só trava numero/valor/vencimento em parcelas que já existem (geradas
        # automaticamente). Numa linha nova adicionada manualmente esses campos
        # ficam editáveis, senão o Postgres rejeita o INSERT (NOT NULL).
        if obj is not None:
            return ("numero", "valor", "vencimento")
        return ()

    def has_add_permission(self, request, obj=None):
        # Parcelas devem ser criadas via Emprestimo.gerar_parcelas() (ajustando
        # qtd_parcelas e salvando) ou recriadas pelo shell/comando de management,
        # nunca digitadas à mão aqui — evita numero/valor/vencimento inconsistentes.
        return False


@admin.register(Emprestimo)
class EmprestimoAdmin(admin.ModelAdmin):
    list_display = ("cotista", "ciclo", "valor_principal", "taxa_juros", "qtd_parcelas", "status")
    list_filter = ("status", "ciclo")
    search_fields = ("cotista__nome",)
    inlines = [ParcelaInline]
    readonly_fields = ("aviso_parcelas",)

    def aviso_parcelas(self, obj):
        if obj and obj.pk and obj.qtd_parcelas != obj.parcelas.count():
            return (
                f"⚠ qtd_parcelas ({obj.qtd_parcelas}) não bate com o número de parcelas "
                f"cadastradas ({obj.parcelas.count()}). Para recriar as parcelas, use: "
                f"emp.parcelas.all().delete(); emp.gerar_parcelas() no shell "
                f"(isso reseta pagamentos já registrados nessas parcelas)."
            )
        return "Ok"
    aviso_parcelas.short_description = "Consistência de parcelas"

    def save_model(self, request, obj, form, change):
        is_new = obj.pk is None
        super().save_model(request, obj, form, change)
        if is_new:
            obj.gerar_parcelas()


@admin.register(Parcela)
class ParcelaAdmin(admin.ModelAdmin):
    list_display = ("emprestimo", "numero", "valor", "vencimento", "pago", "multa_valor")
    list_filter = ("pago", "vencimento")


class PagamentoRifaInline(admin.TabularInline):
    model = PagamentoRifa
    extra = 0


@admin.register(RifaMensal)
class RifaMensalAdmin(admin.ModelAdmin):
    list_display = ("titulo", "mes_referencia", "valor_bilhete", "arrecadacao_liquida", "total_pendentes")
    list_filter = ("ciclo",)
    inlines = [PagamentoRifaInline]
    actions = ["gerar_cobranca_todos_cotistas"]

    @admin.action(description="Gerar cobrança (1 bilhete) para todos os cotistas ativos")
    def gerar_cobranca_todos_cotistas(self, request, queryset):
        total_criadas = 0
        for rifa in queryset:
            for cotista in Cotista.objects.filter(status=Cotista.ATIVO):
                _, criada = PagamentoRifa.objects.get_or_create(rifa=rifa, cotista=cotista)
                total_criadas += 1 if criada else 0
        self.message_user(request, f"{total_criadas} cobrança(s) de rifa criada(s).", level=messages.SUCCESS)


@admin.register(PagamentoRifa)
class PagamentoRifaAdmin(admin.ModelAdmin):
    list_display = ("cotista", "rifa", "valor", "pago", "data_pagamento")
    list_filter = ("rifa", "pago")
    search_fields = ("cotista__nome",)


@admin.register(Investimento)
class InvestimentoAdmin(admin.ModelAdmin):
    list_display = ("descricao", "valor_aplicado", "rendimento_apurado", "data_aplicacao", "data_resgate")


@admin.register(Movimentacao)
class MovimentacaoAdmin(admin.ModelAdmin):
    list_display = ("data", "tipo", "origem", "valor", "cotista_relacionado", "ciclo")
    list_filter = ("tipo", "origem", "ciclo")
    date_hierarchy = "data"


@admin.register(Rateio)
class RateioAdmin(admin.ModelAdmin):
    list_display = ("ciclo", "cotista", "capital_cotas", "lucro_distribuido", "saldo_final")
    list_filter = ("ciclo",)
    readonly_fields = ("data_calculo",)


@admin.register(LogAuditoria)
class LogAuditoriaAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "usuario", "acao", "tabela", "registro_id")
    list_filter = ("acao", "tabela")
    readonly_fields = [f.name for f in LogAuditoria._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
