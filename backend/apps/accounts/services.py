"""A regra de cada rota da conta e da gestao de usuarios, como servico (M2.1a, fase 1).

A fase 1 nao tem rota HTTP (D-107): as views da fase 2 chamam estas funcoes e traduzem o
`AccountError` para a resposta. Os servicos que mexem na sessao recebem o `HttpRequest`; os
de gestao recebem quem pede (`actor`) e o IP.

**Transacao.** Todo servico que grava evento grava o evento e a mudanca num unico
`transaction.atomic()` (RF-24): a mudanca sem o evento nao existe. `login_failed` e
`login_throttled`, que nao mudam nada, gravam sozinhos. O cache do bloqueio fica fora das
transacoes -- nao e transacional.

**Nada aqui importa `rest_framework`** (`test_fase1_sem_drf`).
"""

from __future__ import annotations

import secrets
from typing import Any

from django.contrib.auth import authenticate, update_session_auth_hash
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.http import HttpRequest

from apps.accounts import lockout
from apps.accounts.audit import record
from apps.accounts.errors import AccountError
from apps.accounts.managers import UserManager
from apps.accounts.models import AccessEvent, Organization, User

# As restricoes de unicidade do e-mail: a do `unique=True` da `0001` e a de `Lower(email)`
# da `0003`. Outro `IntegrityError` -- o `slug` da organizacao pessoal, numa corrida
# improvavel -- sobe sem virar `email_taken`.
_EMAIL_CONSTRAINTS = frozenset({"user_email_key", "user_email_lower_uniq"})

INVALID_CREDENTIALS_MESSAGE = "E-mail ou senha incorretos."


def normalize_email(value: str) -> str:
    """Minusculas inteiras e sem espaco nas pontas (RF-08)."""
    return UserManager.normalize_email(value)


def _ip(request: HttpRequest) -> str | None:
    return request.META.get("REMOTE_ADDR") or None


def me_body(user: User) -> dict[str, Any]:
    """O corpo `me`, lista fechada (RF-09)."""
    org = user.organization
    return {
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "must_change_password": user.must_change_password,
        "is_staff": user.is_staff,
        "organization": {
            "name": org.name,
            "slug": org.slug,
            "is_personal": org.is_personal,
        },
    }


def user_body(user: User) -> dict[str, Any]:
    """O corpo `user` da gestao, lista fechada (RF-14)."""
    return {
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "is_active": user.is_active,
        "must_change_password": user.must_change_password,
        "created_at": user.created_at,
        "last_login": user.last_login,
    }


def _invalid(fields: dict[str, list[str]]) -> AccountError:
    return AccountError("invalid_parameter", "Dados inválidos.", {"fields": fields})


def _is_email_violation(exc: IntegrityError) -> bool:
    diag = getattr(exc.__cause__, "diag", None)
    return getattr(diag, "constraint_name", None) in _EMAIL_CONSTRAINTS


def _email_taken() -> AccountError:
    return AccountError("email_taken", "Este e-mail já tem conta.", {})


def _validate_identity(email: str, name: str) -> dict[str, list[str]]:
    fields: dict[str, list[str]] = {}
    try:
        validate_email(email)
    except ValidationError:
        fields["email"] = ["Informe um e-mail válido."]
    if not name or len(name) > 120:
        fields["name"] = ["Informe um nome de 1 a 120 caracteres."]
    return fields


def _personal_slug() -> str:
    while True:
        slug = f"pessoal-{secrets.token_hex(6)}"
        if not Organization.objects.filter(slug=slug).exists():
            return slug


# --- a conta ---------------------------------------------------------------------------


def signup(request: HttpRequest, *, email: str, name: str, password: str) -> User:
    """Cadastro aberto: organizacao pessoal, usuario `admin` dela, sessao aberta (RF-09).

    Nao consulta a existencia antes: grava e deixa a unicidade do banco decidir, e o
    `IntegrityError` do e-mail vira `email_taken` -- o e-mail repetido e o cadastro
    concorrente sao o mesmo caminho.
    """
    email = normalize_email(email)
    name = name.strip()
    fields = _validate_identity(email, name)
    try:
        validate_password(password, User(email=email, name=name))
    except ValidationError as exc:
        fields["password"] = list(exc.messages)
    if fields:
        raise _invalid(fields)
    try:
        with transaction.atomic():
            org = Organization.objects.create(
                name=name, slug=_personal_slug(), is_personal=True
            )
            user = User.objects.create_user(
                email=email,
                name=name,
                organization=org,
                password=password,
                role=User.Role.ADMIN,
            )
            django_login(request, user)
            record(
                AccessEvent.Kind.SIGNUP,
                email=email,
                actor=user,
                organization=org,
                ip=_ip(request),
            )
    except IntegrityError as exc:
        if _is_email_violation(exc):
            raise _email_taken() from exc
        raise
    return user


def login(request: HttpRequest, *, email: str, password: str) -> User:
    """Entrada (RF-10). O bloqueio e consultado **antes** da senha (RF-22b)."""
    email = normalize_email(email)
    ip = _ip(request)
    wait = lockout.blocked_for(email, ip)
    target = User.objects.filter(email=email).select_related("organization").first()
    if wait > 0:
        record(
            AccessEvent.Kind.LOGIN_THROTTLED,
            email=email,
            target=target,
            organization=target.organization if target else None,
            ip=ip,
            details={"wait_seconds": wait},
        )
        raise AccountError(
            "too_many_requests",
            "Muitas tentativas. Tente de novo mais tarde.",
            {"wait_seconds": wait},
        )
    user = authenticate(request, email=email, password=password)
    if user is None:
        lockout.register_failure(email, ip)
        record(
            AccessEvent.Kind.LOGIN_FAILED,
            email=email,
            target=target,
            organization=target.organization if target else None,
            ip=ip,
            details={"reason": "invalid_credentials"},
        )
        raise AccountError("invalid_credentials", INVALID_CREDENTIALS_MESSAGE, {})
    assert isinstance(user, User)
    lockout.clear(email, ip)
    with transaction.atomic():
        django_login(request, user)
        record(
            AccessEvent.Kind.LOGIN,
            email=user.email,
            actor=user,
            organization=user.organization,
            ip=ip,
        )
    return user


def _current_user(request: HttpRequest) -> User:
    user = request.user
    if not user.is_authenticated:
        raise AccountError("not_authenticated", "Entre para continuar.", {})
    assert isinstance(user, User)
    return user


def logout(request: HttpRequest) -> None:
    """Saida (RF-11): o evento e o fim da sessao na mesma transacao."""
    user = _current_user(request)
    with transaction.atomic():
        record(
            AccessEvent.Kind.LOGOUT,
            email=user.email,
            actor=user,
            organization=user.organization,
            ip=_ip(request),
        )
        django_logout(request)


def me(request: HttpRequest) -> dict[str, Any]:
    """Quem sou eu; aceito com `must_change_password`."""
    return me_body(_current_user(request))


def change_password(
    request: HttpRequest, *, current_password: str, new_password: str
) -> None:
    """Troca de senha (RF-13): mantem esta sessao e derruba as outras do usuario."""
    user = _current_user(request)
    if not user.check_password(current_password):
        raise AccountError("invalid_credentials", "Senha atual incorreta.", {})
    if new_password == current_password:
        raise _invalid(
            {"new_password": ["A nova senha precisa ser diferente da atual."]}
        )
    try:
        validate_password(new_password, user)
    except ValidationError as exc:
        raise _invalid({"new_password": list(exc.messages)}) from exc
    with transaction.atomic():
        user.set_password(new_password)
        user.must_change_password = False
        user.save(update_fields=["password", "must_change_password"])
        update_session_auth_hash(request, user)
        record(
            AccessEvent.Kind.PASSWORD_CHANGED,
            email=user.email,
            actor=user,
            organization=user.organization,
            ip=_ip(request),
        )

