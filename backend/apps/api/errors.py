"""O formato de erro da API (D-86): `{"error": {"code", "message", "details"}}`.

`handle_exception` e o `EXCEPTION_HANDLER` do DRF. O mapeamento e uma lista fechada; o que
nao estiver nela vira 500 `internal_error`, com mensagem generica. O tratador **nunca**
devolve `None`: com `None`, o DRF relanca a excecao, e com `DEBUG` ligado o Django
mostraria a pagina de depuracao, com o traceback.
"""

from __future__ import annotations

import logging
from typing import Any

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.http import Http404
from rest_framework.exceptions import (
    APIException,
    MethodNotAllowed,
    NotAcceptable,
    NotFound,
    ParseError,
    PermissionDenied,
    UnsupportedMediaType,
)
from rest_framework.response import Response
from rest_framework.views import set_rollback

logger = logging.getLogger(__name__)


class ApiError(APIException):
    """A excecao de negocio da API: leva o status, o codigo, a mensagem e os detalhes."""

    def __init__(
        self,
        status: int,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(detail=message, code=code)
        self.status_code = status
        self.error_code = code
        self.error_message = message
        self.error_details: dict[str, Any] = {} if details is None else details


def _body(
    code: str, message: str, details: dict[str, Any] | None = None
) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": {} if details is None else details,
        }
    }


def _method(context: dict[str, Any]) -> str:
    request = context.get("request")
    method = getattr(request, "method", None)
    return method if isinstance(method, str) else "?"


def handle_exception(exc: Exception, context: dict[str, Any]) -> Response:
    """Traduz a excecao para o formato da D-86. Lista fechada; o resto e 500."""
    status: int
    code: str
    message: str
    details: dict[str, Any] = {}

    if isinstance(exc, ApiError):
        status, code, message = exc.status_code, exc.error_code, exc.error_message
        details = exc.error_details
    elif isinstance(exc, Http404 | NotFound):
        status, code, message = 404, "not_found", "Recurso não encontrado."
    elif isinstance(exc, MethodNotAllowed):
        status, code = 405, "method_not_allowed"
        message = f"Método {_method(context)} não permitido nesta rota."
    elif isinstance(exc, NotAcceptable):
        status, code = 406, "not_acceptable"
        message = "Formato de resposta não aceito: a API só responde em JSON."
    elif isinstance(exc, UnsupportedMediaType):
        status, code = 415, "unsupported_media_type"
        message = "Formato do corpo não suportado: a API só aceita JSON."
    elif isinstance(exc, PermissionDenied | DjangoPermissionDenied):
        status, code = 403, "permission_denied"
        message = "Sem permissão para acessar este recurso."
    elif isinstance(exc, ParseError):
        status, code = 400, "invalid_parameter"
        message = "O corpo do pedido não é JSON válido."
    else:
        logger.exception("erro nao previsto na API")
        status, code = 500, "internal_error"
        message = "Erro interno. Tente de novo mais tarde."

    set_rollback()
    return Response(_body(code, message, details), status=status)
