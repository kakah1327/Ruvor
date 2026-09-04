import os

from django.db import connection
from django.test import Client
from pytest_django.plugin import DjangoDbBlocker


def test_health_responde_ok(client: Client) -> None:
    resposta = client.get("/health")
    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok"}


def test_conexao_com_o_banco(django_db_blocker: DjangoDbBlocker) -> None:
    """Abre um cursor contra o banco *configurado*.

    Nao usa @pytest.mark.django_db de proposito: aquela marca alcanca o servidor, mas
    conecta em test_<nome>, e por isso nao exercita RUVOR_DB_NAME — um nome errado no
    .env passaria despercebido. Desbloquear o acesso a mao e o que mantem o banco real.
    """
    with django_db_blocker.unblock(), connection.cursor() as cursor:
        cursor.execute("SELECT current_database()")
        linha = cursor.fetchone()

    assert linha is not None
    assert linha[0] == os.environ["RUVOR_DB_NAME"]
