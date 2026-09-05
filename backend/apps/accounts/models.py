"""Organizacao e usuario do projeto, as duas primeiras tabelas do esquema `core`.

O esquema vai embutido no `db_table`, com aspas no meio: o Django 6.1 nao tem opcao de
esquema, e `quote_name` do backend do PostgreSQL nao requota identificador que ja tem
aspas. E o contrato da D-38 — mudar as aspas muda o esquema em que a tabela nasce.

A chave primaria nao e declarada: o `DEFAULT_AUTO_FIELD` do Django 6.1 ja e
`BigAutoField` (conferido no `django.conf.global_settings` do conteiner).
"""

from __future__ import annotations

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models

from apps.accounts.managers import UserManager


class Organization(models.Model):
    """Dono do dado (D-08). O `slug` e a chave estavel de referencia, nunca o `id`."""

    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=60, unique=True)
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
    """

    email = models.EmailField(max_length=254, unique=True)
    name = models.CharField(max_length=120)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="users",
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    # O `USERNAME_FIELD` nunca entra em `REQUIRED_FIELDS` — e o que o `auth.E002`
    # reprova. A organizacao tambem fica de fora: `createsuperuser` passaria a chave
    # primaria crua, e resolver isso e do M2.1, que constroi o fluxo de autenticacao.
    REQUIRED_FIELDS = ["name"]

    class Meta:
        db_table = 'core"."user'

    def __str__(self) -> str:
        return self.email
