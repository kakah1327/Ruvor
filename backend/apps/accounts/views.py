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

import re
from typing import Any, ClassVar

from django.middleware.csrf import get_token
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from drf_spectacular.views import SpectacularJSONAPIView
from rest_framework.exceptions import APIException, Throttled, ValidationError
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
from apps.accounts.permissions import AccountReady
from apps.accounts.serializers import (
    ApiKeyCreateIn,
    ApiKeyListOut,
    ApiKeyWithSecretOut,
    LoginIn,
    MeOut,
    PasswordIn,
    SignupIn,
    UserCreateIn,
    UserListOut,
    UserOut,
    UserUpdateIn,
    UserWithPasswordOut,
)
from apps.api.errors import ApiError

# So digitos, com sinal opcional: o `int()` sozinho aceitaria espaco e sublinhado.
_INTEGER = re.compile(r"[+-]?\d+")

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
    "api_key_not_found": 404,  # M4.2
    "api_key_limit": 409,
    "report_not_found": 404,  # M4.1
    "risk_not_calculated": 409,
    "asset_not_found": 404,
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
    api_key_scope: ClassVar[str | None] = None  # M4.2, RF-07: a chave nao alcanca

    @extend_schema(responses={204: None})
    def get(self, request: Request) -> Response:
        get_token(request._request)
        return Response(status=204)


class SignupView(APIView):
    """`POST auth/signup`: cadastro com organizacao pessoal (RF-09)."""

    permission_classes = [AllowAny]  # noqa: RUF012 -- a forma do DRF; o V-09 le do corpo
    api_key_scope: ClassVar[str | None] = None  # M4.2, RF-07: a chave nao alcanca
    throttle_classes = [AuthRateThrottle]  # noqa: RUF012 -- idem

    @extend_schema(request=SignupIn, responses={201: MeOut})
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
    api_key_scope: ClassVar[str | None] = None  # M4.2, RF-07: a chave nao alcanca
    throttle_classes = [AuthRateThrottle]  # noqa: RUF012 -- idem

    @extend_schema(request=LoginIn, responses={200: MeOut})
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
    api_key_scope: ClassVar[str | None] = None  # M4.2, RF-07: a chave nao alcanca

    @extend_schema(request=None, responses={204: None})
    def post(self, request: Request) -> Response:
        try:
            services.logout(request._request)
        except AccountError as err:
            raise account_error_to_api(err) from err
        return Response(status=204)


class MeView(APIView):
    """`GET auth/me`: quem esta logado, aceito com senha provisoria."""

    permission_classes = [IsAuthenticated]  # noqa: RUF012 -- a forma do DRF; o V-09 le do corpo
    api_key_scope: ClassVar[str | None] = None  # M4.2, RF-07: a chave nao alcanca

    @extend_schema(responses={200: MeOut})
    def get(self, request: Request) -> Response:
        return Response(services.me_body(_user(request)))


def _query_int(request: Request, name: str, default: int) -> int:
    """Um inteiro da query string; ausente, o padrao. A faixa e conferida pelo servico."""
    raw = request.query_params.get(name)
    if raw is None:
        return default
    if not _INTEGER.fullmatch(raw):
        raise ApiError(
            400,
            "invalid_parameter",
            f"O parâmetro {name} precisa ser um número inteiro.",
            {"parameter": name},
        )
    return int(raw)


class OrganizationUsersView(APIView):
    """`GET organization/users` lista e `POST` cria (RF-15, RF-16)."""

    permission_classes = [AccountReady]  # noqa: RUF012 -- a forma do DRF; o V-09 le do corpo
    api_key_scope: ClassVar[str | None] = None  # M4.2, RF-07: a chave nao alcanca

    @extend_schema(
        parameters=[
            OpenApiParameter("limit", OpenApiTypes.INT, default=50),
            OpenApiParameter("offset", OpenApiTypes.INT, default=0),
        ],
        responses={200: UserListOut},
    )
    def get(self, request: Request) -> Response:
        limit = _query_int(request, "limit", 50)
        offset = _query_int(request, "offset", 0)
        try:
            count, users = services.list_users(
                _user(request), limit=limit, offset=offset
            )
        except AccountError as err:
            raise account_error_to_api(err) from err
        return Response(
            {
                "count": count,
                "limit": limit,
                "offset": offset,
                "results": [services.user_body(u) for u in users],
            }
        )

    @extend_schema(request=UserCreateIn, responses={201: UserWithPasswordOut})
    def post(self, request: Request) -> Response:
        data = _data(UserCreateIn, request)
        try:
            user, password = services.create_user(
                _user(request), ip=services._ip(request._request), **data
            )
        except AccountError as err:
            raise account_error_to_api(err) from err
        return Response(
            {"user": services.user_body(user), "temporary_password": password},
            status=201,
        )


class OrganizationUserView(APIView):
    """`PATCH organization/users/{email}`: papel e/ou ativo (RF-17)."""

    permission_classes = [AccountReady]  # noqa: RUF012 -- a forma do DRF; o V-09 le do corpo
    api_key_scope: ClassVar[str | None] = None  # M4.2, RF-07: a chave nao alcanca

    @extend_schema(request=UserUpdateIn, responses={200: UserOut})
    def patch(self, request: Request, email: str) -> Response:
        changes = request.data
        if not isinstance(changes, dict):
            raise ValidationError("O corpo precisa ser um objeto JSON.")
        try:
            user = services.update_user(
                _user(request),
                email,
                changes=changes,
                ip=services._ip(request._request),
            )
        except AccountError as err:
            raise account_error_to_api(err) from err
        return Response(services.user_body(user))


class TemporaryPasswordView(APIView):
    """`POST organization/users/{email}/temporary-password` (RF-18)."""

    permission_classes = [AccountReady]  # noqa: RUF012 -- a forma do DRF; o V-09 le do corpo
    api_key_scope: ClassVar[str | None] = None  # M4.2, RF-07: a chave nao alcanca

    @extend_schema(request=None, responses={200: UserWithPasswordOut})
    def post(self, request: Request, email: str) -> Response:
        try:
            user, password = services.reset_temporary_password(
                _user(request), email, ip=services._ip(request._request)
            )
        except AccountError as err:
            raise account_error_to_api(err) from err
        return Response(
            {"user": services.user_body(user), "temporary_password": password}
        )


class PasswordView(APIView):
    """`POST auth/password`: troca a propria senha (RF-13)."""

    permission_classes = [IsAuthenticated]  # noqa: RUF012 -- a forma do DRF; o V-09 le do corpo
    api_key_scope: ClassVar[str | None] = None  # M4.2, RF-07: a chave nao alcanca
    throttle_classes = [AuthRateThrottle]  # noqa: RUF012 -- idem

    @extend_schema(request=PasswordIn, responses={204: None})
    def post(self, request: Request) -> Response:
        data = _data(PasswordIn, request)
        try:
            services.change_password(request._request, **data)
        except AccountError as err:
            raise account_error_to_api(err) from err
        return Response(status=204)


class ApiKeysView(APIView):
    """`GET api-keys` lista as proprias chaves e `POST` cria uma (M4.2, RF-03, RF-04)."""

    permission_classes = [AccountReady]  # noqa: RUF012 -- a forma do DRF; o V-09 le do corpo
    api_key_scope: ClassVar[str | None] = None  # RF-07: a chave nao gere chave

    @extend_schema(responses={200: ApiKeyListOut})
    def get(self, request: Request) -> Response:
        keys = services.list_api_keys(_user(request))
        return Response({"results": [services.api_key_body(k) for k in keys]})

    @extend_schema(request=ApiKeyCreateIn, responses={201: ApiKeyWithSecretOut})
    def post(self, request: Request) -> Response:
        data = _data(ApiKeyCreateIn, request)
        try:
            key, secret = services.create_api_key(
                _user(request), ip=services._ip(request._request), **data
            )
        except AccountError as err:
            raise account_error_to_api(err) from err
        return Response(
            {"api_key": services.api_key_body(key), "secret": secret}, status=201
        )


class ApiKeyView(APIView):
    """`DELETE api-keys/{prefix}`: revoga a propria chave (M4.2, RF-05)."""

    permission_classes = [AccountReady]  # noqa: RUF012 -- a forma do DRF; o V-09 le do corpo
    api_key_scope: ClassVar[str | None] = None  # RF-07: a chave nao gere chave

    @extend_schema(responses={204: None})
    def delete(self, request: Request, prefix: str) -> Response:
        try:
            services.revoke_api_key(
                _user(request), prefix, ip=services._ip(request._request)
            )
        except AccountError as err:
            raise account_error_to_api(err) from err
        return Response(status=204)


class SchemaView(SpectacularJSONAPIView):
    """`GET schema`: o esquema OpenAPI 3 da API, em JSON (M4.2, RF-12). A chave le."""

    permission_classes = [AllowAny]  # noqa: RUF012 -- a forma do DRF; o V-09 le do corpo
    api_key_scope: ClassVar[str | None] = "read"  # RF-07: a chave le (so metodo seguro)
