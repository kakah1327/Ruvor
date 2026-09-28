"""V-09: toda view sob `api/` declara `permission_classes` no proprio corpo (D-86).

O padrao do `REST_FRAMEWORK` e `IsAuthenticated`: a view que esquecesse a sua nasceria
fechada, e o teste o confere tambem. Mas "herdou o padrao" e exatamente o que nao pode
passar: por isso a pergunta e `"permission_classes" in view_class.__dict__` — declarado na
classe, nao achado por heranca. Ligar o login no M2.1 e trocar a classe declarada, nao
procurar rota aberta.
"""

from __future__ import annotations

from collections.abc import Iterator

from django.conf import settings
from django.urls import URLPattern, URLResolver, get_resolver

from apps.api import views


def _rotas(
    padroes: list[URLPattern | URLResolver], prefixo: str = ""
) -> Iterator[tuple[str, URLPattern]]:
    """Percorre o resolvedor em profundidade: `(rota inteira, padrao)` de cada folha."""
    for padrao in padroes:
        rota = prefixo + str(padrao.pattern).lstrip("^")
        if isinstance(padrao, URLResolver):
            yield from _rotas(padrao.url_patterns, rota)
        else:
            yield rota, padrao


def _views_da_api() -> dict[str, type]:
    achadas: dict[str, type] = {}
    for rota, padrao in _rotas(get_resolver("config.urls").url_patterns):
        if rota.startswith("api/"):
            achadas[rota] = padrao.callback.view_class  # type: ignore[attr-defined]
    return achadas


def test_toda_view_sob_api_declara_a_permissao_no_proprio_corpo() -> None:
    achadas = _views_da_api()

    # contra a varredura inerte: as rotas de leitura e a view final estao todas aqui
    assert {
        views.AssetListView,
        views.AssetDetailView,
        views.AssetPricesView,
        views.AssetEventsView,
        views.AssetMetricsView,
        views.ApiNotFound,
    } <= set(achadas.values())

    sem_declaracao = sorted(
        f"{rota} -> {classe.__name__}"
        for rota, classe in achadas.items()
        if "permission_classes" not in classe.__dict__
    )
    assert not sem_declaracao, "sem permission_classes no corpo: " + "; ".join(
        sem_declaracao
    )


def test_a_permissao_padrao_e_is_authenticated() -> None:
    assert settings.REST_FRAMEWORK["DEFAULT_PERMISSION_CLASSES"] == [
        "rest_framework.permissions.IsAuthenticated"
    ]
