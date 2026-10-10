"""
Gera a cobrança de rifa (1 bilhete por cotista) para todos os cotistas ativos,
para uma rifa mensal específica.

Uso:
    docker compose exec web python manage.py gerar_cobranca_rifa "Rifa de Setembro"
"""
from django.core.management.base import BaseCommand, CommandError

from core.models import RifaMensal, Cotista, PagamentoRifa


class Command(BaseCommand):
    help = "Gera a cobrança (1 bilhete) de uma rifa mensal para todos os cotistas ativos."

    def add_arguments(self, parser):
        parser.add_argument(
            "titulo",
            type=str,
            help="Título exato da RifaMensal (como cadastrado no admin).",
        )

    def handle(self, *args, **options):
        titulo = options["titulo"]
        try:
            rifa = RifaMensal.objects.get(titulo=titulo)
        except RifaMensal.DoesNotExist:
            raise CommandError(f"Rifa '{titulo}' não encontrada.")
        except RifaMensal.MultipleObjectsReturned:
            raise CommandError(f"Mais de uma rifa com o título '{titulo}'. Renomeie para ficarem únicos.")

        criadas, existentes = 0, 0
        for cotista in Cotista.objects.filter(status=Cotista.ATIVO):
            _, foi_criada = PagamentoRifa.objects.get_or_create(rifa=rifa, cotista=cotista)
            criadas += 1 if foi_criada else 0
            existentes += 0 if foi_criada else 1

        self.stdout.write(self.style.SUCCESS(
            f"Rifa '{rifa.titulo}': {criadas} cobrança(s) criada(s), {existentes} já existiam."
        ))
