"""M2.1a, T5: nada do teste `transaction=True` sobra para os testes seguintes.

O `flush` do fim do `transaction=True` nao limpa as tabelas com esquema no `db_table`
([aprendizados](../../../docs/aprendizados.md)): quem limpa e a fixture de modulo
`restaura_dados_de_migracao`. Este teste, **sem marca de banco**, roda depois dos
transacionais (o pytest-django os ordena assim) e confere o banco de teste: nenhum usuario,
nenhum evento, so a `ruvor` e o Ibovespa. Sem ele, esvaziar a fixture passaria em silencio.

Fora da suite inteira -- rodando este arquivo sozinho, sem banco de teste criado -- a conexao
aponta para o banco configurado, que tem dado de verdade; ai o teste nao diz nada e pula.
"""

from __future__ import annotations

import pytest
from django.db import connection
from pytest_django.plugin import DjangoDbBlocker

from apps.accounts.models import AccessEvent, Organization, User
from apps.assets.models import Asset


def test_nada_sobra_do_teste_transacional(django_db_blocker: DjangoDbBlocker) -> None:
    with django_db_blocker.unblock():
        if not connection.settings_dict["NAME"].startswith("test_"):
            pytest.skip("sem banco de teste: so faz sentido na suite inteira")
        assert User.objects.count() == 0
        assert AccessEvent.objects.count() == 0
        assert list(Organization.objects.values_list("slug", flat=True)) == ["ruvor"]
        assert Asset.objects.filter(ticker="IBOV").count() == 1
