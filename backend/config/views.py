from django.http import HttpRequest, JsonResponse


def health(request: HttpRequest) -> JsonResponse:
    """Rota de saude: sem autenticacao, sem banco. Contrato congelado na spec."""
    return JsonResponse({"status": "ok"})
