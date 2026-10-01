"""Os corpos de entrada das rotas de conta (M2.1a, fase 2).

So presenca e tipo: a regra de conteudo -- e-mail valido, nome, forca da senha -- continua nos
servicos, que juntam os erros por campo.

Os `*Out` e o `UserUpdateIn` sao **so descricao**, para o esquema OpenAPI (M4.2, RF-12): os
corpos continuam sendo os dicts dos servicos, e o `PATCH` continua mandando o corpo inteiro ao
servico. Por isso `allow_blank=True` e `trim_whitespace=False`:
o texto chega ao servico como veio. Campo ausente vira `ValidationError`, que o tratador de
`apps/api/errors.py` responde como 400 `invalid_parameter`, com `details.fields`.
"""

from __future__ import annotations

from rest_framework import serializers

from apps.accounts.models import User


def _text() -> serializers.CharField:
    return serializers.CharField(allow_blank=True, trim_whitespace=False)


class SignupIn(serializers.Serializer[None]):
    email = _text()
    name = _text()
    password = _text()


class LoginIn(serializers.Serializer[None]):
    email = _text()
    password = _text()


class UserCreateIn(serializers.Serializer[None]):
    email = _text()
    name = _text()
    role = _text()


class PasswordIn(serializers.Serializer[None]):
    current_password = _text()
    new_password = _text()


class ApiKeyCreateIn(serializers.Serializer[None]):
    name = _text()  # M4.2, RF-03: aparado pelo servico


class UserUpdateIn(serializers.Serializer[None]):
    role = serializers.ChoiceField(choices=User.Role.choices, required=False)
    is_active = serializers.BooleanField(required=False)


# --- os corpos de saida, so descricao (M4.2, RF-12) ---------------------------------------


class OrganizationOut(serializers.Serializer[None]):
    name = serializers.CharField()
    slug = serializers.CharField()
    is_personal = serializers.BooleanField()


class MeOut(serializers.Serializer[None]):
    """`me_body`."""

    email = serializers.EmailField()
    name = serializers.CharField()
    role = serializers.ChoiceField(choices=User.Role.choices)
    must_change_password = serializers.BooleanField()
    is_staff = serializers.BooleanField()
    organization = OrganizationOut()


class UserOut(serializers.Serializer[None]):
    """`user_body`."""

    email = serializers.EmailField()
    name = serializers.CharField()
    role = serializers.ChoiceField(choices=User.Role.choices)
    is_active = serializers.BooleanField()
    must_change_password = serializers.BooleanField()
    created_at = serializers.DateTimeField()
    last_login = serializers.DateTimeField(allow_null=True)


class UserListOut(serializers.Serializer[None]):
    count = serializers.IntegerField()
    limit = serializers.IntegerField()
    offset = serializers.IntegerField()
    results = UserOut(many=True)


class UserWithPasswordOut(serializers.Serializer[None]):
    user = UserOut()
    temporary_password = serializers.CharField()


class ApiKeyOut(serializers.Serializer[None]):
    """`api_key_body`."""

    prefix = serializers.CharField()
    name = serializers.CharField()
    scopes = serializers.ListField(child=serializers.CharField())
    created_at = serializers.DateTimeField()
    last_used_at = serializers.DateTimeField(allow_null=True)


class ApiKeyListOut(serializers.Serializer[None]):
    results = ApiKeyOut(many=True)


class ApiKeyWithSecretOut(serializers.Serializer[None]):
    api_key = ApiKeyOut()
    secret = serializers.CharField()


# --- os relatorios (M4.1) ---------------------------------------------------------------


class ReportCreateIn(serializers.Serializer[None]):
    """So a presenca: o tipo e do servico, que da `invalid_parameter` a numero (RF-05)."""

    ticker = _text()


class ReportRequesterOut(serializers.Serializer[None]):
    email = serializers.EmailField()
    name = serializers.CharField()


class ReportOut(serializers.Serializer[None]):
    """`report_body`. `kind` e `CharField`, o que a spec fixou: descrito como texto."""

    id = serializers.UUIDField()
    kind = serializers.CharField()
    format_version = serializers.IntegerField()
    ticker = serializers.CharField()
    as_of_date = serializers.DateField()
    risk_run_id = serializers.IntegerField()
    sha256 = serializers.CharField()
    size_bytes = serializers.IntegerField()
    created_at = serializers.DateTimeField()
    requested_by = ReportRequesterOut()


class ReportOneOut(serializers.Serializer[None]):
    report = ReportOut()


class ReportListOut(serializers.Serializer[None]):
    count = serializers.IntegerField()
    limit = serializers.IntegerField()
    offset = serializers.IntegerField()
    results = ReportOut(many=True)
