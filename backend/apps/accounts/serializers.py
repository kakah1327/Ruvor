"""Os corpos de entrada das rotas de conta (M2.1a, fase 2).

So presenca e tipo: a regra de conteudo -- e-mail valido, nome, forca da senha -- continua nos
servicos, que juntam os erros por campo. Por isso `allow_blank=True` e `trim_whitespace=False`:
o texto chega ao servico como veio. Campo ausente vira `ValidationError`, que o tratador de
`apps/api/errors.py` responde como 400 `invalid_parameter`, com `details.fields`.
"""

from __future__ import annotations

from rest_framework import serializers


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
