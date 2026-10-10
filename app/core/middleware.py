from .signals import set_usuario_atual


class AuditoriaUsuarioMiddleware:
    """Guarda o usuário da request atual numa variável thread-local,
    pra que os signals de auditoria (que não têm acesso à request)
    consigam registrar quem fez cada alteração."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        usuario = request.user if request.user.is_authenticated else None
        set_usuario_atual(usuario)
        response = self.get_response(request)
        set_usuario_atual(None)
        return response
