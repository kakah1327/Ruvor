"""M4.2: o contexto da organizacao e o middleware que o zera (RF-13; V-17).

As partes que precisam de modelo -- o gerente aplicado a `ApiKey` -- entram com a tabela.
"""

from __future__ import annotations

import pytest
from django.http import HttpRequest, HttpResponse
from django.test import RequestFactory

from apps.accounts.tenancy import (
    OrganizationScopeMiddleware,
    current_organization_id,
    organization_scope,
    set_organization_id,
)


def test_organization_scope_poe_e_restaura() -> None:
    assert current_organization_id() is None
    with organization_scope(7):
        assert current_organization_id() == 7
    assert current_organization_id() is None


def test_organization_scope_aninhado_restaura_o_de_fora() -> None:
    with organization_scope(3):
        with organization_scope(7):
            assert current_organization_id() == 7
        assert current_organization_id() == 3
    assert current_organization_id() is None


def test_organization_scope_restaura_mesmo_com_excecao() -> None:
    with pytest.raises(ValueError), organization_scope(7):
        raise ValueError("falha dentro do escopo")
    assert current_organization_id() is None


def test_middleware_zera_no_comeco() -> None:
    visto: list[int | None] = []

    def get_response(request: HttpRequest) -> HttpResponse:
        visto.append(current_organization_id())
        return HttpResponse()

    set_organization_id(9)
    OrganizationScopeMiddleware(get_response)(RequestFactory().get("/"))
    assert visto == [None]


def test_middleware_zera_no_fim() -> None:
    def get_response(request: HttpRequest) -> HttpResponse:
        set_organization_id(5)
        return HttpResponse()

    OrganizationScopeMiddleware(get_response)(RequestFactory().get("/"))
    assert current_organization_id() is None


def test_middleware_zera_no_fim_mesmo_com_excecao() -> None:
    def get_response(request: HttpRequest) -> HttpResponse:
        set_organization_id(5)
        raise RuntimeError("a view falhou")

    with pytest.raises(RuntimeError):
        OrganizationScopeMiddleware(get_response)(RequestFactory().get("/"))
    assert current_organization_id() is None
