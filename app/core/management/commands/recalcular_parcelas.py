"""
Recalcula o valor das parcelas NÃO PAGAS de empréstimos existentes, aplicando
a fórmula corrigida de juros simples mensal (J = C x i x n).

Só mexe em parcelas com pago=False — parcelas já pagas não são alteradas,
para não reescrever um histórico do que já foi efetivamente recebido.

Uso:
    # Recalcula todos os empréstimos não quitados
    docker compose exec web python manage.py recalcular_parcelas

    # Recalcula só os empréstimos de um cotista específico
    docker compose exec web python manage.py recalcular_parcelas --cotista "Juciara Da Silva Do Espirito Santo Duarte"
"""
from django.core.management.base import BaseCommand

from core.models import Emprestimo


class Command(BaseCommand):
    help = "Recalcula o valor das parcelas não pagas com a fórmula corrigida de juros simples mensal."

    def add_arguments(self, parser):
        parser.add_argument(
            "--cotista", type=str, default=None,
            help="Nome exato do cotista, para recalcular só os empréstimos dele.",
        )

    def handle(self, *args, **options):
        emprestimos = Emprestimo.objects.exclude(status=Emprestimo.QUITADO)
        if options["cotista"]:
            emprestimos = emprestimos.filter(cotista__nome=options["cotista"])

        total_emprestimos_alterados = 0
        total_parcelas_alteradas = 0

        for emp in emprestimos:
            parcelas_nao_pagas = emp.parcelas.filter(pago=False)
            qtd = parcelas_nao_pagas.count()
            if qtd == 0:
                continue

            novo_valor_parcela = emp.valor_parcela  # já usa a fórmula corrigida (property)
            alterou = False
            for parcela in parcelas_nao_pagas:
                if parcela.valor != novo_valor_parcela:
                    self.stdout.write(
                        f"  Parcela {parcela.numero} - R${parcela.valor} -> R${novo_valor_parcela}"
                    )
                    parcela.valor = novo_valor_parcela
                    parcela.save(update_fields=["valor"])
                    total_parcelas_alteradas += 1
                    alterou = True

            if alterou:
                total_emprestimos_alterados += 1
                self.stdout.write(self.style.SUCCESS(
                    f"Empréstimo {emp.cotista.nome} ({emp.data_emprestimo:%d/%m/%Y}) - "
                    f"novo total com juros: R${emp.valor_total_com_juros}\n"
                ))

        self.stdout.write(self.style.SUCCESS(
            f"\nConcluído: {total_emprestimos_alterados} empréstimo(s) e "
            f"{total_parcelas_alteradas} parcela(s) recalculada(s)."
        ))
