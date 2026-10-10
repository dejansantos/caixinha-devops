"""
Gera as cotas de TODOS os meses do ciclo de uma vez (do mês de início até o mês de fim),
para todos os cotistas ativos ou para um cotista específico (útil pra backfill de quem
entrou depois do início do ciclo).

Uso:
    # Gera todos os meses do ciclo aberto, para todos os cotistas ativos
    docker compose exec web python manage.py gerar_cotas_ciclo

    # Gera todos os meses do ciclo, só para um cotista específico
    docker compose exec web python manage.py gerar_cotas_ciclo --cotista "Samara Cosme Souza"

    # Especificando o ciclo (se houver mais de um)
    docker compose exec web python manage.py gerar_cotas_ciclo --ciclo "Caixinha 2026"
"""
from dateutil.relativedelta import relativedelta

from django.core.management.base import BaseCommand, CommandError

from core.models import CicloAnual, Cotista, Cota


class Command(BaseCommand):
    help = "Gera as cotas de todos os meses do ciclo (início ao fim) para todos os cotistas ativos, ou um específico."

    def add_arguments(self, parser):
        parser.add_argument(
            "--ciclo", type=str, default=None,
            help="Nome exato do CicloAnual. Se omitido, usa o ciclo com status Aberto.",
        )
        parser.add_argument(
            "--cotista", type=str, default=None,
            help="Nome exato do cotista, para gerar só pra ele (backfill de quem entrou depois).",
        )

    def handle(self, *args, **options):
        if options["ciclo"]:
            try:
                ciclo = CicloAnual.objects.get(nome=options["ciclo"])
            except CicloAnual.DoesNotExist:
                raise CommandError(f"Ciclo '{options['ciclo']}' não encontrado.")
        else:
            ciclo = CicloAnual.objects.filter(status=CicloAnual.ABERTO).first()
            if not ciclo:
                raise CommandError("Nenhum ciclo aberto encontrado. Use --ciclo 'Nome do Ciclo' para especificar.")

        if options["cotista"]:
            try:
                cotistas = [Cotista.objects.get(nome=options["cotista"])]
            except Cotista.DoesNotExist:
                raise CommandError(f"Cotista '{options['cotista']}' não encontrado.")
        else:
            cotistas = list(Cotista.objects.filter(status=Cotista.ATIVO))

        # monta a lista de meses do ciclo (dia 1 de cada mês, do início ao fim)
        meses = []
        mes_atual = ciclo.data_inicio.replace(day=1)
        fim = ciclo.data_fim.replace(day=1)
        while mes_atual <= fim:
            meses.append(mes_atual)
            mes_atual += relativedelta(months=1)

        criadas, existentes = 0, 0
        for cotista in cotistas:
            for mes_referencia in meses:
                _, foi_criada = Cota.objects.get_or_create(
                    cotista=cotista, ciclo=ciclo, mes_referencia=mes_referencia,
                )
                criadas += 1 if foi_criada else 0
                existentes += 0 if foi_criada else 1

        self.stdout.write(self.style.SUCCESS(
            f"Ciclo '{ciclo.nome}' ({len(meses)} meses, {ciclo.data_inicio:%m/%Y} a {ciclo.data_fim:%m/%Y}) "
            f"para {len(cotistas)} cotista(s): {criadas} cota(s) criada(s), {existentes} já existiam."
        ))
