"""M2.1a, T13: toda view que exige conta declara `AccountReady` (RF-29; V-21).

`IsAuthenticated` puro so serve as tres rotas que quem tem senha provisoria precisa usar --
`me`, `password` e `logout` (RF-07). Qualquer outra view sob `api/v1/` que o declare deixaria
a proxima rota (M2.2) aceitar conta com senha por trocar, em silencio.
"""

from __future__ import annotations

from collections.abc import Iterator

from django.urls import URLPattern, URLResolver, get_resolver
from rest_framework.permissions import IsAuthenticated

from apps.accounts import views
from apps.accounts.permissions import AccountReady

SO_AUTENTICADO = {views.MeView, views.PasswordView, views.LogoutView}
GESTAO = {
    views.OrganizationUsersView,
    views.OrganizationUserView,
    views.TemporaryPasswordView,
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
        if rota.startswith("api/v1/") and classe is not None:
            achadas.add(classe)
    return achadas


def test_is_authenticated_so_em_me_password_e_logout() -> None:
    achadas = _views_da_api()
    # contra a varredura inerte: as de conta e as de gestao estao todas aqui
    assert SO_AUTENTICADO | GESTAO <= achadas

    fora = sorted(
        classe.__name__
        for classe in achadas - SO_AUTENTICADO
        if IsAuthenticated in classe.__dict__.get("permission_classes", [])
    )
    assert not fora, "IsAuthenticated fora de me, password e logout: " + ", ".join(fora)


def test_as_rotas_de_gestao_declaram_account_ready() -> None:
    for classe in GESTAO:
        assert AccountReady in classe.__dict__["permission_classes"], classe.__name__
