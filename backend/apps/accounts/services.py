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
from django.contrib.sessions.models import Session
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils import timezone

from apps.accounts import lockout
from apps.accounts.audit import record
from apps.accounts.errors import AccountError
from apps.accounts.managers import UserManager
from apps.accounts.models import AccessEvent, Organization, User
from apps.accounts.passwords import generate_temporary_password

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


# --- a gestao de usuarios da organizacao ------------------------------------------------

_UPDATABLE = frozenset({"role", "is_active"})


def _after_org_lock() -> None:
    """Costura dos testes concorrentes: roda logo depois da trava da organizacao."""


def _check_manager(actor: User) -> User:
    """Quem pode gerir, nesta ordem (RF-14). Rele o ator do banco: o objeto de quem chama
    pode estar velho -- e, depois da trava do `update_user`, e o que ve o papel novo."""
    actor = User.objects.select_related("organization").get(pk=actor.pk)
    if actor.must_change_password:
        raise AccountError(
            "password_change_required", "Troque a senha provisória para continuar.", {}
        )
    if actor.role != User.Role.ADMIN:
        raise AccountError(
            "permission_denied",
            "Só a administração da organização pode fazer isso.",
            {},
        )
    if actor.organization.is_personal:
        raise AccountError(
            "personal_organization",
            "Organização pessoal não tem gestão de usuários.",
            {},
        )
    return actor


def _org_users(actor: User) -> QuerySet[User]:
    """A **unica** origem de consulta de usuario da gestao (RF-15): so a organizacao de quem
    pede. E o "outro meio" de isolar usuario que a D-41 pede."""
    return User.objects.filter(organization_id=actor.organization_id)


def _get_target(actor: User, email: str) -> User:
    try:
        target = _org_users(actor).get(email=normalize_email(email))
    except User.DoesNotExist:
        # O mesmo corpo para inexistente e de outra organizacao: nao confirma o e-mail.
        raise AccountError("user_not_found", "Usuário não encontrado.", {}) from None
    return target


def _drop_sessions(user: User) -> None:
    """Apaga as sessoes vivas do usuario -- sem isso, reativar ressuscitaria as antigas.
    Percorre as sessoes vivas: linear no numero delas, declarado no plano."""
    alvo = str(user.pk)
    for session in Session.objects.filter(expire_date__gt=timezone.now()):
        if session.get_decoded().get("_auth_user_id") == alvo:
            session.delete()


def list_users(
    actor: User, *, limit: int = 50, offset: int = 0
) -> tuple[int, list[User]]:
    """Os usuarios da organizacao de quem pede, por e-mail (RF-15)."""
    actor = _check_manager(actor)
    if not 1 <= limit <= 100:
        raise AccountError(
            "invalid_parameter", "`limit` vai de 1 a 100.", {"parameter": "limit"}
        )
    if offset < 0:
        raise AccountError(
            "invalid_parameter",
            "`offset` não pode ser negativo.",
            {"parameter": "offset"},
        )
    usuarios = _org_users(actor).order_by("email")
    return usuarios.count(), list(usuarios[offset : offset + limit])


def create_user(
    actor: User, *, email: str, name: str, role: str, ip: str | None
) -> tuple[User, str]:
    """Cria o usuario com senha provisoria, mostrada so aqui (RF-16)."""
    actor = _check_manager(actor)
    email = normalize_email(email)
    name = name.strip()
    fields = _validate_identity(email, name)
    if role not in User.Role.values:
        fields["role"] = ["Papel deve ser admin ou member."]
    if fields:
        raise _invalid(fields)
    senha = generate_temporary_password()
    try:
        with transaction.atomic():
            user = User.objects.create_user(
                email=email,
                name=name,
                organization=actor.organization,
                password=senha,
                role=role,
                must_change_password=True,
            )
            record(
                AccessEvent.Kind.USER_CREATED,
                email=email,
                actor=actor,
                target=user,
                organization=actor.organization,
                ip=ip,
                details={"role": role},
            )
    except IntegrityError as exc:
        if _is_email_violation(exc):
            raise _email_taken() from exc
        raise
    return user, senha


def _validate_changes(changes: dict[str, object]) -> None:
    fields: dict[str, list[str]] = {}
    for campo in sorted(set(changes) - _UPDATABLE):
        fields[campo] = ["campo desconhecido"]
    if "role" in changes and changes["role"] not in User.Role.values:
        fields["role"] = ["Papel deve ser admin ou member."]
    if "is_active" in changes and not isinstance(changes["is_active"], bool):
        fields["is_active"] = ["Deve ser verdadeiro ou falso."]
    if fields:
        raise _invalid(fields)


def update_user(
    actor: User, email: str, *, changes: dict[str, object], ip: str | None
) -> User:
    """Muda papel e/ou ativo (RF-17). A organizacao nunca fica sem `admin` ativo: a linha
    dela e travada antes de contar, e duas administradoras rebaixando uma a outra ao mesmo
    tempo terminam com uma."""
    _validate_changes(changes)
    with transaction.atomic():
        Organization.objects.select_for_update().get(pk=actor.organization_id)
        _after_org_lock()
        actor = _check_manager(actor)
        target = _get_target(actor, email)
        antes = {"role": target.role, "is_active": target.is_active}
        depois = {**antes, **{campo: changes[campo] for campo in changes}}
        mudou = {
            campo: {"before": antes[campo], "after": depois[campo]}
            for campo in sorted(antes)
            if antes[campo] != depois[campo]
        }
        if not mudou:
            return target
        era_admin = antes["role"] == User.Role.ADMIN and antes["is_active"]
        segue_admin = depois["role"] == User.Role.ADMIN and depois["is_active"]
        if era_admin and not segue_admin:
            outros = (
                _org_users(actor)
                .filter(role=User.Role.ADMIN, is_active=True)
                .exclude(pk=target.pk)
            )
            if not outros.exists():
                raise AccountError(
                    "last_admin",
                    "A organização precisa de ao menos uma administração ativa.",
                    {},
                )
        target.role = str(depois["role"])
        target.is_active = bool(depois["is_active"])
        target.save(update_fields=["role", "is_active"])
        if antes["is_active"] and not target.is_active:
            _drop_sessions(target)
        record(
            AccessEvent.Kind.USER_UPDATED,
            email=target.email,
            actor=actor,
            target=target,
            organization=actor.organization,
            ip=ip,
            details=mudou,
        )
    return target


def reset_temporary_password(
    actor: User, email: str, *, ip: str | None
) -> tuple[User, str]:
    """Senha provisoria nova para outro usuario da organizacao (RF-18)."""
    actor = _check_manager(actor)
    target = _get_target(actor, email)
    if target.pk == actor.pk:
        raise AccountError(
            "use_password_route", "Troque a própria senha pela troca de senha.", {}
        )
    senha = generate_temporary_password()
    with transaction.atomic():
        target.set_password(senha)
        target.must_change_password = True
        target.save(update_fields=["password", "must_change_password"])
        _drop_sessions(target)
        record(
            AccessEvent.Kind.TEMPORARY_PASSWORD_RESET,
            email=target.email,
            actor=actor,
            target=target,
            organization=actor.organization,
            ip=ip,
        )
    return target, senha
