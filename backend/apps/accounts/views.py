"""As rotas de conta sob `/api/v1/` (M2.1a, fase 2; D-86, D-100).

Cada view traduz o pedido HTTP para um servico de `apps/accounts/services.py` e o
`AccountError` dele para o erro da API (`account_error_to_api`). A regra mora nos servicos; a
view so confere CSRF, forma do corpo e permissao.

**O CSRF do `signup` e do `login`** e conferido na propria view, **antes** de ler o corpo: a
`SessionAuthentication` so o exige de quem ja esta logado (RF-04).

**O limite `auth`** (RF-21) conta por IP em `signup`, `login` e `password`. Nao e o
`ScopedRateThrottle`: aquele conta pelo usuario quando ha login, e o `password` so serve a
quem esta logado. Roda no `initial()` do DRF, antes da view -- falha de CSRF tambem conta.
"""

from __future__ import annotations

from typing import Any

from django.middleware.csrf import get_token
from rest_framework.exceptions import APIException, Throttled
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView

from apps.accounts import services
from apps.accounts.authentication import SessionAuthentication
from apps.accounts.errors import AccountError
from apps.accounts.models import User
from apps.accounts.serializers import LoginIn, PasswordIn, SignupIn
from apps.api.errors import ApiError

# O status de cada codigo de `AccountError` (RF-27). `too_many_requests` fica fora: vira
# `Throttled`, que leva o `Retry-After` (RF-22b). Codigo fora dos dois e defeito de programa:
# `KeyError`, que o tratador responde como 500.
STATUS_BY_CODE: dict[str, int] = {
    "invalid_parameter": 400,
    "invalid_credentials": 400,
    "not_authenticated": 401,
    "permission_denied": 403,
    "password_change_required": 403,
    "user_not_found": 404,
    "email_taken": 409,
    "personal_organization": 409,
    "last_admin": 409,
    "use_password_route": 409,
}


def account_error_to_api(err: AccountError) -> APIException:
    """O `AccountError` como excecao da API: `ApiError`, ou `Throttled` no bloqueio."""
    if err.code == "too_many_requests":
        return Throttled(wait=err.details["wait_seconds"])
    return ApiError(STATUS_BY_CODE[err.code], err.code, err.message, err.details)


class AuthRateThrottle(SimpleRateThrottle):
    """O limite `auth`: `DEFAULT_THROTTLE_RATES["auth"]` pedidos por IP (RF-21)."""

    scope = "auth"

    def get_cache_key(self, request: Request, view: APIView) -> str:
        return self.cache_format % {
            "scope": self.scope,
            "ident": self.get_ident(request),
        }


def _data(serializer_class: type[Serializer[None]], request: Request) -> dict[str, Any]:
    serializer = serializer_class(data=request.data)
    serializer.is_valid(raise_exception=True)
    data: dict[str, Any] = serializer.validated_data
    return data


def _user(request: Request) -> User:
    user = request.user
    assert isinstance(user, User)
    return user


class CsrfView(APIView):
    """`GET auth/csrf`: garante o cookie `csrftoken` (RF-04)."""

    permission_classes = [AllowAny]  # noqa: RUF012 -- a forma do DRF; o V-09 le do corpo

    def get(self, request: Request) -> Response:
        get_token(request._request)
        return Response(status=204)


class SignupView(APIView):
    """`POST auth/signup`: cadastro com organizacao pessoal (RF-09)."""

    permission_classes = [AllowAny]  # noqa: RUF012 -- a forma do DRF; o V-09 le do corpo
    throttle_classes = [AuthRateThrottle]  # noqa: RUF012 -- idem

    def post(self, request: Request) -> Response:
        SessionAuthentication().enforce_csrf(request)
        data = _data(SignupIn, request)
        try:
            user = services.signup(request._request, **data)
        except AccountError as err:
            raise account_error_to_api(err) from err
        return Response(services.me_body(user), status=201)


class LoginView(APIView):
    """`POST auth/login` (RF-10). O `login()` do Django troca o `csrftoken`."""

    permission_classes = [AllowAny]  # noqa: RUF012 -- a forma do DRF; o V-09 le do corpo
    throttle_classes = [AuthRateThrottle]  # noqa: RUF012 -- idem

    def post(self, request: Request) -> Response:
        SessionAuthentication().enforce_csrf(request)
        data = _data(LoginIn, request)
        try:
            user = services.login(request._request, **data)
        except AccountError as err:
            raise account_error_to_api(err) from err
        return Response(services.me_body(user))


class LogoutView(APIView):
    """`POST auth/logout` (RF-11)."""

    permission_classes = [IsAuthenticated]  # noqa: RUF012 -- a forma do DRF; o V-09 le do corpo

    def post(self, request: Request) -> Response:
        try:
            services.logout(request._request)
        except AccountError as err:
            raise account_error_to_api(err) from err
        return Response(status=204)


class MeView(APIView):
    """`GET auth/me`: quem esta logado, aceito com senha provisoria."""

    permission_classes = [IsAuthenticated]  # noqa: RUF012 -- a forma do DRF; o V-09 le do corpo

    def get(self, request: Request) -> Response:
        return Response(services.me_body(_user(request)))


class PasswordView(APIView):
    """`POST auth/password`: troca a propria senha (RF-13)."""

    permission_classes = [IsAuthenticated]  # noqa: RUF012 -- a forma do DRF; o V-09 le do corpo
    throttle_classes = [AuthRateThrottle]  # noqa: RUF012 -- idem

    def post(self, request: Request) -> Response:
        data = _data(PasswordIn, request)
        try:
            services.change_password(request._request, **data)
        except AccountError as err:
            raise account_error_to_api(err) from err
        return Response(status=204)
