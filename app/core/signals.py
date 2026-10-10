"""
Signals de auditoria.

Registra automaticamente em LogAuditoria toda criação, edição e exclusão
nos models sensíveis: Emprestimo, Parcela, Movimentacao, Rateio.

Como funciona:
- pre_save: busca o estado "antes" no banco (se o registro já existir)
- post_save: compara com o estado "depois" e grava o log (criação ou edição)
- post_delete: grava o log de exclusão com o estado final antes de sumir

O usuário responsável é capturado via middleware (core/middleware.py),
que guarda o usuário da request atual numa variável thread-local.
"""
import threading
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.forms.models import model_to_dict

from .models import Emprestimo, Parcela, Movimentacao, Rateio, LogAuditoria

_MODELOS_AUDITADOS = (Emprestimo, Parcela, Movimentacao, Rateio)

_thread_locals = threading.local()


def get_usuario_atual():
    return getattr(_thread_locals, "usuario", None)


def set_usuario_atual(usuario):
    _thread_locals.usuario = usuario


def _serializar(instance):
    """Converte a instância em dict simples (só campos de valor, sem relações reversas)."""
    dados = model_to_dict(instance)
    # normaliza tipos não serializáveis diretamente (Decimal, date, etc.)
    import json
    return json.loads(json.dumps(dados, cls=DjangoJSONEncoder, default=str))


@receiver(pre_save)
def guardar_estado_anterior(sender, instance, **kwargs):
    if sender not in _MODELOS_AUDITADOS:
        return
    if not instance.pk:
        instance._estado_anterior = None
        return
    try:
        anterior = sender.objects.get(pk=instance.pk)
        instance._estado_anterior = _serializar(anterior)
    except sender.DoesNotExist:
        instance._estado_anterior = None


@receiver(post_save)
def logar_criacao_ou_edicao(sender, instance, created, **kwargs):
    if sender not in _MODELOS_AUDITADOS:
        return
    LogAuditoria.objects.create(
        usuario=get_usuario_atual(),
        acao="criar" if created else "editar",
        tabela=sender.__name__,
        registro_id=instance.pk,
        valores_antes=getattr(instance, "_estado_anterior", None),
        valores_depois=_serializar(instance),
    )


@receiver(post_delete)
def logar_exclusao(sender, instance, **kwargs):
    if sender not in _MODELOS_AUDITADOS:
        return
    LogAuditoria.objects.create(
        usuario=get_usuario_atual(),
        acao="excluir",
        tabela=sender.__name__,
        registro_id=instance.pk,
        valores_antes=_serializar(instance),
        valores_depois=None,
    )
