"""O formato de erro da API (D-86): `{"error": {"code", "message", "details"}}`.

`handle_exception` e o `EXCEPTION_HANDLER` do DRF. O mapeamento e uma lista fechada; o que
nao estiver nela vira 500 `internal_error`, com mensagem generica. O tratador **nunca**
devolve `None`: com `None`, o DRF relanca a excecao, e com `DEBUG` ligado o Django
mostraria a pagina de depuracao, com o traceback.

Desde a fase 2 do M2.1a, a lista ganha tres linhas (RF-27 da spec do M2.1a):

- `NotAuthenticated` -> 401 `not_authenticated`, com o `WWW-Authenticate` que a `APIView` pos
  em `exc.auth_header`. O status sai de `exc.status_code`, e nao fixo: sem autenticador que de
  cabecalho, a `APIView` rebaixa a excecao a 403, e ai ela e `permission_denied`;
- `ValidationError` -> 400 `invalid_parameter`, com os erros por campo em `details.fields`;
- `Throttled` -> 429 `too_many_requests`, com `Retry-After` e `details.wait_seconds`.

E, desde o M4.2 (RF-11), `AuthenticationFailed` -> 401 `invalid_api_key`, pela mesma regra do
`NotAuthenticated`: e o que a autenticacao por chave levanta.

Os cabecalhos sao postos aqui porque quem os copiaria da excecao e o `exception_handler`
padrao do DRF, que este tratador substitui.
"""

from __future__ import annotations

import logging
import math
from typing import Any

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.http import Http404
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    MethodNotAllowed,
    NotAcceptable,
    NotAuthenticated,
    NotFound,
    ParseError,
    PermissionDenied,
    Throttled,
    UnsupportedMediaType,
    ValidationError,
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


def _fields(detail: Any) -> dict[str, list[str]]:
    """Os erros de um `ValidationError` como `{campo: [mensagens]}`, em texto puro."""
    if isinstance(detail, dict):
        return {
            str(field): [str(item) for item in messages]
            if isinstance(messages, list)
            else [str(messages)]
            for field, messages in detail.items()
        }
    items = detail if isinstance(detail, list) else [detail]
    return {"non_field_errors": [str(item) for item in items]}


def handle_exception(exc: Exception, context: dict[str, Any]) -> Response:
    """Traduz a excecao para o formato da D-86. Lista fechada; o resto e 500."""
    status: int
    code: str
    message: str
    details: dict[str, Any] = {}
    headers: dict[str, str] = {}

    if isinstance(exc, ApiError):
        status, code, message = exc.status_code, exc.error_code, exc.error_message
        details = exc.error_details
    elif isinstance(exc, NotAuthenticated) and exc.status_code == 401:
        status, code, message = 401, "not_authenticated", "Entre para continuar."
        auth_header = getattr(exc, "auth_header", None)
        if auth_header:
            headers["WWW-Authenticate"] = str(auth_header)
    elif isinstance(exc, AuthenticationFailed) and exc.status_code == 401:
        # a chave de API recusada (M4.2, RF-11): a mesma regra do `NotAuthenticated`
        status, code, message = 401, "invalid_api_key", "Chave de API inválida."
        auth_header = getattr(exc, "auth_header", None)
        if auth_header:
            headers["WWW-Authenticate"] = str(auth_header)
    elif isinstance(exc, NotAuthenticated | AuthenticationFailed):
        # rebaixado a 403 pela `APIView`: nenhum autenticador deu `WWW-Authenticate`
        status, code = 403, "permission_denied"
        message = "Sem permissão para acessar este recurso."
    elif isinstance(exc, ValidationError):
        status, code, message = 400, "invalid_parameter", "Dados inválidos."
        details = {"fields": _fields(exc.detail)}
    elif isinstance(exc, Throttled):
        status, code = 429, "too_many_requests"
        message = "Muitas tentativas. Aguarde e tente de novo."
        # os stubs do DRF nao declaram `wait`, que o `Throttled.__init__` sempre poe
        raw_wait = getattr(exc, "wait", None)
        wait = None if raw_wait is None else math.ceil(raw_wait)
        details = {"wait_seconds": wait}
        if wait is not None:
            headers["Retry-After"] = str(wait)
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
    return Response(_body(code, message, details), status=status, headers=headers)
