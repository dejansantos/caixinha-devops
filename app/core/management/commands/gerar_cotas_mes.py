"""
Gera a cota mensal de todos os cotistas ativos para um mês específico.

Uso:
    docker compose exec web python manage.py gerar_cotas_mes 2026-09

Se não passar o ciclo, usa o ciclo com status "Aberto" automaticamente.
"""
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError

from core.models import CicloAnual, Cotista, Cota


class Command(BaseCommand):
    help = "Gera a cota mensal de todos os cotistas ativos para um mês/ano específico (formato YYYY-MM)."

    def add_arguments(self, parser):
        parser.add_argument(
            "mes",
            type=str,
            help="Mês/ano no formato YYYY-MM. Ex: 2026-09 para setembro de 2026.",
        )
        parser.add_argument(
            "--ciclo",
            type=str,
            default=None,
            help="Nome exato do CicloAnual a usar. Se omitido, usa o ciclo com status Aberto.",
        )

    def handle(self, *args, **options):
        mes_str = options["mes"]
        try:
            mes_referencia = datetime.strptime(mes_str, "%Y-%m").date().replace(day=1)
        except ValueError:
            raise CommandError(f"Formato de mês inválido: '{mes_str}'. Use YYYY-MM, ex: 2026-09.")

        if options["ciclo"]:
            try:
                ciclo = CicloAnual.objects.get(nome=options["ciclo"])
            except CicloAnual.DoesNotExist:
                raise CommandError(f"Ciclo '{options['ciclo']}' não encontrado.")
        else:
            ciclo = CicloAnual.objects.filter(status=CicloAnual.ABERTO).first()
            if not ciclo:
                raise CommandError("Nenhum ciclo aberto encontrado. Use --ciclo 'Nome do Ciclo' para especificar.")

        criadas, existentes = 0, 0
        for cotista in Cotista.objects.filter(status=Cotista.ATIVO):
            _, foi_criada = Cota.objects.get_or_create(
                cotista=cotista, ciclo=ciclo, mes_referencia=mes_referencia,
            )
            criadas += 1 if foi_criada else 0
            existentes += 0 if foi_criada else 1

        self.stdout.write(self.style.SUCCESS(
            f"Ciclo '{ciclo.nome}' — {mes_referencia:%m/%Y}: "
            f"{criadas} cota(s) criada(s), {existentes} já existiam."
        ))
