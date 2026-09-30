"""M2.1m, T1: a coluna do autor do pedido, `core.compute_request.requested_by` (RF-01; V-01, V-02).

- **V-01**: a coluna existe no banco, `bigint` e anulavel -- quem a cria e a `0002`.
- **V-02**: o `PROTECT` barra apagar o autor, com o pedido entre os objetos protegidos (o
  `User` tem outros vinculos `PROTECT`, e o erro nao pode vir deles); o pedido sem autor
  grava nulo.
"""

from __future__ import annotations

import pytest
from django.db import connection
from django.db.models import ProtectedError
from django.utils import timezone

from apps.api.models import ComputeRequest
from apps.assets.models import Asset
from tests.accounts.conftest import organizacao, usuario

pytestmark = pytest.mark.django_db


def _ativo(ticker: str) -> Asset:
    agora = timezone.now()
    return Asset.objects.create(
        ticker=ticker,
        kind=Asset.Kind.STOCK,
        name=f"{ticker} S.A.",
        trading_name=ticker,
        status=Asset.Status.ACTIVE,
        provider_symbol=f"{ticker}.SA",
        created_at=agora,
        updated_at=agora,
    )


def test_v01_a_coluna_requested_by_id() -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT data_type, is_nullable FROM information_schema.columns"
            " WHERE table_schema = 'core' AND table_name = 'compute_request'"
            " AND column_name = 'requested_by_id'"
        )
        linhas = cursor.fetchall()
    assert linhas == [("bigint", "YES")]


def test_v02_o_autor_do_pedido_nao_se_apaga() -> None:
    autor = usuario(organizacao("acme"), "autor@acme.test")
    pedido = ComputeRequest.objects.create(
        asset=_ativo("ABCD3"),
        status=ComputeRequest.Status.QUEUED,
        requested_at=timezone.now(),
        requested_by=autor,
    )
    with pytest.raises(ProtectedError) as erro:
        autor.delete()
    assert pedido in erro.value.protected_objects


def test_v02_o_pedido_sem_autor_grava_nulo() -> None:
    pedido = ComputeRequest.objects.create(
        asset=_ativo("ABCD3"),
        status=ComputeRequest.Status.QUEUED,
        requested_at=timezone.now(),
    )
    pedido.refresh_from_db()
    assert pedido.requested_by_id is None
