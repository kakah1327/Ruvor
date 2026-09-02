import pytest
from django.core.exceptions import ImproperlyConfigured
from django.db import connection
from django.test import Client


def test_health_responde_ok(client: Client) -> None:
    resposta = client.get("/health")
    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok"}


def test_processo_nao_tem_banco() -> None:
    """F2b-02: nao ha banco configurado, e qualquer acesso falha alto."""
    with pytest.raises(ImproperlyConfigured):
        connection.cursor()
