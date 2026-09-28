"""Organizacao e usuario do projeto, as duas primeiras tabelas do esquema `core`.

O esquema vai embutido no `db_table`, com aspas no meio: o Django 6.1 nao tem opcao de
esquema, e `quote_name` do backend do PostgreSQL nao requota identificador que ja tem
aspas. E o contrato da D-38 — mudar as aspas muda o esquema em que a tabela nasce.

A chave primaria nao e declarada: o `DEFAULT_AUTO_FIELD` do Django 6.1 ja e
`BigAutoField` (conferido no `django.conf.global_settings` do conteiner).
"""

from __future__ import annotations

from typing import Any, ClassVar

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone

from apps.accounts.managers import UserManager


class Organization(models.Model):
    """Dono do dado (D-08). O `slug` e a chave estavel de referencia, nunca o `id`."""

    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=60, unique=True)
    # A organizacao pessoal implicita da D-24, de quem se cadastrou sozinho: um usuario so,
    # `admin`, sem gestao de usuarios (M2.1a, RF-06). A `ruvor` e real.
    is_personal = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core"."organization'

    def __str__(self) -> str:
        return self.name


class User(AbstractBaseUser, PermissionsMixin):
    """Usuario do projeto, apontado por `AUTH_USER_MODEL` e autenticado por e-mail.

    Herda `AbstractBaseUser` e `PermissionsMixin`, e nao `AbstractUser` (D-39): o
    `username` do `AbstractUser` seria justamente a migracao cara que este bloco evita.
    De `AbstractBaseUser` vem `password` e `last_login`; de `PermissionsMixin` vem
    `is_superuser`, `groups` e `user_permissions`.

    O e-mail e guardado em minusculas, e o banco garante a unicidade sem diferenca de
    caixa (M2.1a, RF-08). `role` e o papel **na organizacao**; `is_staff` e
    `is_superuser` sao da plataforma e nao dao poder em organizacao nenhuma (RF-05).
    """

    class Role(models.TextChoices):
        ADMIN = "admin"
        MEMBER = "member"

    email = models.EmailField(max_length=254, unique=True)
    name = models.CharField(max_length=120)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="users",
    )
    # Sem `default`: quem cria diz o papel, e o gerente poe `member` quando nao vem.
    role = models.CharField(max_length=10, choices=Role)
    # Senha posta por outra pessoa (a administradora, o comando): so a troca libera (RF-07).
    must_change_password = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    # O `USERNAME_FIELD` nunca entra em `REQUIRED_FIELDS` — e o que o `auth.E002`
    # reprova. A organizacao tambem fica de fora: `createsuperuser` passaria a chave
    # primaria crua. Sem organizacao, o gerente poe o superusuario na `ruvor` (D-105).
    REQUIRED_FIELDS: ClassVar[list[str]] = ["name"]

    class Meta:
        db_table = 'core"."user'
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(Lower("email"), name="user_email_lower_uniq"),
        ]

    def __str__(self) -> str:
        return self.email


class AccessEventQuerySet(models.QuerySet["AccessEvent"]):
    """Recusa as escritas em massa: a auditoria so cresce (RF-25)."""

    def update(self, **kwargs: Any) -> int:
        raise TypeError("access_event so cresce")

    def delete(self) -> tuple[int, dict[str, int]]:
        raise TypeError("access_event so cresce")


class AccessEvent(models.Model):
    """Um evento de acesso ou de alteracao de usuario (M2.1a, RF-23 e RF-24, D-104).

    Uma linha por evento, gravada na mesma transacao da mudanca que descreve, e **nunca**
    alterada nem apagada. Nenhuma rota le a tabela neste bloco: o filtro por organizacao
    (D-41) e do primeiro bloco que a ler. Nunca guarda senha.
    """

    class Kind(models.TextChoices):
        SIGNUP = "signup"
        LOGIN = "login"
        LOGIN_FAILED = "login_failed"
        LOGIN_THROTTLED = "login_throttled"
        LOGOUT = "logout"
        PASSWORD_CHANGED = "password_changed"
        USER_CREATED = "user_created"
        USER_UPDATED = "user_updated"
        TEMPORARY_PASSWORD_RESET = "temporary_password_reset"

    occurred_at = models.DateTimeField(default=timezone.now)
    kind = models.CharField(max_length=30, choices=Kind)
    actor = models.ForeignKey(
        User, on_delete=models.PROTECT, null=True, related_name="+"
    )
    organization = models.ForeignKey(
        Organization, on_delete=models.PROTECT, null=True, related_name="+"
    )
    target = models.ForeignKey(
        User, on_delete=models.PROTECT, null=True, related_name="+"
    )
    email = models.CharField(max_length=254)
    ip = models.GenericIPAddressField(null=True)
    details = models.JSONField(default=dict)

    objects = AccessEventQuerySet.as_manager()

    class Meta:
        db_table = 'core"."access_event'
        indexes: ClassVar[list[models.Index]] = [
            models.Index(
                fields=["organization", "occurred_at"], name="access_event_org_at"
            ),
            models.Index(fields=["email", "occurred_at"], name="access_event_email_at"),
        ]

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self._state.adding:
            raise TypeError("access_event so cresce")
        super().save(*args, **kwargs)

    def delete(
        self, using: Any = None, keep_parents: bool = False
    ) -> tuple[int, dict[str, int]]:
        raise TypeError("access_event so cresce")
