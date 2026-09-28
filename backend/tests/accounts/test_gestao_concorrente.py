"""M2.1a, T5: duas administradoras rebaixando uma a outra ao mesmo tempo terminam com uma
(RF-17; V-11, concorrencia).

Duas threads, cada uma com a sua conexao, num teste `transaction=True`. A costura
`services._after_org_lock` -- chamada logo depois do `select_for_update` da organizacao --
vira uma barreira de duas partes com `timeout`:

- **com a trava**, a segunda thread fica no `select_for_update` e nunca chega a barreira; a
  barreira estoura por tempo, a primeira segue e confirma, e a segunda, ao pegar a trava,
  rele a si mesma ja `member` e recebe `permission_denied`;
- **sem a trava** (a mutacao), as duas passam pela barreira contando duas `admin`, as duas
  rebaixam, e a organizacao fica sem nenhuma.

O `flush` do `transaction=True` apaga a `ruvor` e o `IBOV`; a fixture de modulo
`restaura_dados_de_migracao` os devolve depois do ultimo teste deste modulo.
"""

from __future__ import annotations

import threading

import pytest
from django.db import connection

from apps.accounts import services
from apps.accounts.errors import AccountError
from apps.accounts.models import User
from tests.accounts.conftest import organizacao, usuario

# `available_apps` e o que faz o `flush` do fim usar `TRUNCATE ... CASCADE`: sem ele, o
# `flush` lista as tabelas pelo `search_path` e nao ve as de juncao do usuario, que moram em
# `core` (`user_user_permissions`), e o `TRUNCATE` de `auth_permission` e recusado.
_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "apps.accounts",
]

pytestmark = [
    pytest.mark.django_db(transaction=True, available_apps=_APPS),
    pytest.mark.usefixtures("restaura_dados_de_migracao"),
]


def test_v11_rebaixamento_cruzado_termina_com_uma_admin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    org = organizacao()
    x = usuario(org, "x@acme.test", role="admin")
    y = usuario(org, "y@acme.test", role="admin")
    barreira = threading.Barrier(2, timeout=2)

    def espera() -> None:
        try:
            barreira.wait()
        except threading.BrokenBarrierError:
            pass

    monkeypatch.setattr(services, "_after_org_lock", espera)
    resultados: dict[str, str] = {}

    def rebaixa(ator: User, alvo: str) -> None:
        try:
            services.update_user(ator, alvo, changes={"role": "member"}, ip=None)
            resultados[alvo] = "ok"
        except AccountError as exc:
            resultados[alvo] = exc.code
        finally:
            connection.close()

    threads = [
        threading.Thread(target=rebaixa, args=(x, "y@acme.test")),
        threading.Thread(target=rebaixa, args=(y, "x@acme.test")),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)

    assert sorted(resultados.values()) == ["ok", "permission_denied"]
    admins = User.objects.filter(organization=org, role="admin", is_active=True)
    assert admins.count() == 1
