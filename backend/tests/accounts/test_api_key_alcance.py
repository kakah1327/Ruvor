"""M4.2, T5: o que a chave alcanca (RF-07; V-07, V-08, V-09).

A chave le as rotas que declaram `api_key_scope = "read"`, e so por metodo seguro. Toda view sob
`api/` declara o atributo no proprio corpo; o padrao, para view sem ele, e recusar -- provado
numa rota de teste fora de `/api/`. A parte de `api-keys` esta em `test_api_key_rotas.py` (T6);
a de `/schema`, em `test_esquema_openapi.py` (T8).
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from django.urls import URLPattern, URLResolver, get_resolver
from rest_framework.test import APIClient

from apps.accounts import services
from apps.accounts import views as conta
from apps.accounts.models import ApiKey, User
from apps.api import views as leitura
from apps.portfolios import views as carteira
from tests.accounts.conftest import organizacao, usuario

SAFE = {"get", "head", "options"}

# as views que a chave le, e as duas que aceitam escrita por outra via (o `POST /risk` e a view
# final): a regra do metodo seguro as barra
LEITURA = {
    leitura.AssetListView,
    leitura.AssetDetailView,
    leitura.AssetPricesView,
    leitura.AssetEventsView,
    leitura.AssetMetricsView,
    leitura.AssetRiskView,
    leitura.AssetFundamentalsView,
    leitura.AssetDisclosuresView,
    leitura.ApiNotFound,
    conta.SchemaView,
    conta.ReportsView,  # M4.1, RF-11: a chave le relatorio
    conta.ReportView,
    conta.ReportJsonView,
    conta.ReportCsvView,
    carteira.PortfoliosView,  # M2.2a, RF-19: a chave le carteira
    carteira.PortfolioView,
    carteira.PortfolioRiskView,
}
ESCRITA_PERMITIDA_COM_READ = {
    leitura.AssetRiskView,
    leitura.ApiNotFound,
    conta.ReportsView,  # o `POST` gera; a regra do metodo seguro o barra
    carteira.PortfoliosView,  # o `POST` cria, o `PATCH` e o `DELETE` mudam: barrados
    carteira.PortfolioView,
    carteira.PortfolioRiskView,  # o `POST` pede; barrado
}
# as que a chave nao alcanca: conta, gestao e as proprias chaves
SEM_CHAVE = {
    conta.CsrfView,
    conta.SignupView,
    conta.LoginView,
    conta.LogoutView,
    conta.MeView,
    conta.PasswordView,
    conta.OrganizationUsersView,
    conta.OrganizationUserView,
    conta.TemporaryPasswordView,
    conta.ApiKeysView,
    conta.ApiKeyView,
    carteira.PortfolioHoldingsView,  # M2.2a, RF-19: so `PUT`
}


def _rotas(
    padroes: list[URLPattern | URLResolver], prefixo: str = ""
) -> Iterator[tuple[str, URLPattern]]:
    for padrao in padroes:
        rota = prefixo + str(padrao.pattern).lstrip("^")
        if isinstance(padrao, URLResolver):
            yield from _rotas(padrao.url_patterns, rota)
        else:
            yield rota, padrao


def _views_da_api() -> set[type]:
    achadas: set[type] = set()
    for rota, padrao in _rotas(get_resolver("config.urls").url_patterns):
        classe = getattr(padrao.callback, "view_class", None)
        if rota.startswith("api/") and classe is not None:
            achadas.add(classe)
    return achadas


def _metodos(classe: type) -> set[str]:
    return {m for m in getattr(classe, "http_method_names", []) if hasattr(classe, m)}


# --- as declaracoes, sobre o resolvedor ---------------------------------------------------


def test_toda_view_sob_api_declara_api_key_scope_no_corpo() -> None:
    achadas = _views_da_api()
    assert LEITURA | SEM_CHAVE <= achadas  # contra a varredura inerte
    sem = sorted(c.__name__ for c in achadas if "api_key_scope" not in c.__dict__)
    assert not sem, "sem api_key_scope no corpo: " + ", ".join(sem)


def test_read_so_com_metodo_seguro_e_conta_e_gestao_com_none() -> None:
    achadas = _views_da_api()
    com_escrita = sorted(
        c.__name__
        for c in achadas - ESCRITA_PERMITIDA_COM_READ
        if c.__dict__.get("api_key_scope") == "read" and _metodos(c) - SAFE
    )
    assert not com_escrita, "read em view que escreve: " + ", ".join(com_escrita)
    for classe in SEM_CHAVE:
        assert classe.__dict__["api_key_scope"] is None, classe.__name__
    for classe in LEITURA:
        assert classe.__dict__["api_key_scope"] == "read", classe.__name__


# --- pela rota ----------------------------------------------------------------------------


@pytest.fixture
def ana() -> User:
    return usuario(organizacao("acme"), "ana@acme.test", role="admin")


@pytest.fixture
def cliente(ana: User) -> APIClient:
    segredo = services.create_api_key(ana, name="minha", ip=None)[1]
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {segredo}")
    return c


def _nao_alcanca(resposta: Any) -> None:
    assert resposta.status_code == 403, resposta.content
    assert resposta.json()["error"]["code"] == "api_key_not_allowed"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "rota",
    [
        "/api/v1/assets",
        "/api/v1/assets/IBOV",
        "/api/v1/assets/IBOV/prices",
        "/api/v1/assets/IBOV/events",
        "/api/v1/assets/IBOV/risk",
        "/api/v1/assets/IBOV/fundamentals",
        "/api/v1/assets/IBOV/disclosures",
    ],
)
def test_v08_a_chave_le_as_rotas_de_leitura(cliente: APIClient, rota: str) -> None:
    resposta = cliente.get(rota)
    assert resposta.status_code == 200, resposta.content


@pytest.mark.django_db
def test_v08_a_chave_nao_escreve_no_risk(cliente: APIClient, debug: bool) -> None:
    _nao_alcanca(cliente.post("/api/v1/assets/IBOV/risk"))


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("metodo", "rota"),
    [
        ("get", "/api/v1/auth/me"),
        ("post", "/api/v1/auth/logout"),
        ("get", "/api/v1/organization/users"),
    ],
)
def test_v08_a_chave_nao_alcanca_conta_nem_gestao(
    cliente: APIClient, metodo: str, rota: str, debug: bool
) -> None:
    _nao_alcanca(getattr(cliente, metodo)(rota))


@pytest.mark.django_db
def test_v08_rota_inexistente_com_chave(cliente: APIClient, debug: bool) -> None:
    resposta = cliente.get("/api/v1/nao-existe")
    assert resposta.status_code == 404
    assert resposta.json()["error"]["code"] == "not_found"
    _nao_alcanca(cliente.post("/api/v1/nao-existe"))


@pytest.mark.django_db
@pytest.mark.urls("tests.accounts.urls_de_teste")
def test_v08_view_sem_o_atributo_recusa_a_chave(cliente: APIClient) -> None:
    _nao_alcanca(cliente.get("/test/sem-escopo"))
    assert APIClient().get("/test/sem-escopo").status_code == 200  # sem chave, passa


@pytest.mark.django_db
def test_v07_o_pedido_recusado_tambem_conta_como_uso(
    ana: User, cliente: APIClient
) -> None:
    _nao_alcanca(cliente.get("/api/v1/auth/me"))
    assert ApiKey.unscoped.get(user=ana).last_used_at is not None


@pytest.mark.django_db
def test_v09_a_chave_nao_passa_pela_checagem_de_csrf(ana: User) -> None:
    segredo = services.create_api_key(ana, name="csrf", ip=None)[1]
    c = APIClient(enforce_csrf_checks=True)
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {segredo}")
    assert c.get("/api/v1/assets").status_code == 200
    # o `POST` prova o eixo: sem token de CSRF, a recusa e do alcance, nao do CSRF
    _nao_alcanca(c.post("/api/v1/assets/IBOV/risk"))
