"""M4.2, T3: duas criacoes simultaneas com 9 chaves ativas terminam com 10 (RF-03; V-03).

Duas threads, cada uma com a sua conexao, num teste `transaction=True`. A costura
`services._after_user_lock` -- chamada logo depois do `select_for_update` da linha da pessoa --
vira uma barreira de duas partes com `timeout`:

- **com a trava**, a segunda thread fica no `select_for_update` e nunca chega a barreira; a
  barreira estoura por tempo, a primeira cria a 10a e confirma, e a segunda, ao pegar a trava,
  conta 10 e recebe `api_key_limit`;
- **sem a trava** (a mutacao), as duas passam pela barreira contando 9, e ficam 11.

Cada thread chama o servico sem contexto de organizacao: o servico se escopa sozinho, e uma
thread nova nao herda o `ContextVar`.
"""

from __future__ import annotations

import threading

import pytest
from django.db import connection

from apps.accounts import services
from apps.accounts.errors import AccountError
from apps.accounts.models import ApiKey
from tests.accounts.conftest import organizacao, usuario
from tests.api.migracao import TRANSACIONAL, banco_limpo  # noqa: F401

pytestmark = [TRANSACIONAL, pytest.mark.usefixtures("banco_limpo")]


def test_v03_duas_criacoes_com_nove_ativas_terminam_com_dez(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ana = usuario(organizacao(), "ana@acme.test")
    for n in range(9):
        services.create_api_key(ana, name=f"k{n}", ip=None)
    barreira = threading.Barrier(2, timeout=2)

    def espera() -> None:
        try:
            barreira.wait()
        except threading.BrokenBarrierError:
            pass

    monkeypatch.setattr(services, "_after_user_lock", espera)
    resultados: list[str] = []

    def cria() -> None:
        try:
            services.create_api_key(ana, name="concorrente", ip=None)
            resultados.append("ok")
        except AccountError as exc:
            resultados.append(exc.code)
        finally:
            connection.close()

    threads = [threading.Thread(target=cria) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)

    assert sorted(resultados) == ["api_key_limit", "ok"]
    ativas = ApiKey.unscoped.filter(user=ana, revoked_at__isnull=True).count()
    assert ativas == 10
