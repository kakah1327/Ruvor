"""A senha provisoria gerada pelo servidor (M2.1a, RF-16).

Mostrada uma vez a quem a pediu e nunca guardada em claro nem registrada. Passa pelos
mesmos validadores da senha escolhida por pessoa (RF-12): gera de novo ate passar.
"""

from __future__ import annotations

import secrets
import string

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

_ALFABETO = string.ascii_letters + string.digits
TAMANHO = 16


def generate_temporary_password() -> str:
    while True:
        senha = "".join(secrets.choice(_ALFABETO) for _ in range(TAMANHO))
        try:
            validate_password(senha)
        except ValidationError:
            continue
        return senha
