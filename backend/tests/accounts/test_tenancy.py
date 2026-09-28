"""M4.2: o filtro automatico por organizacao (RF-13; V-17).

O contexto e o middleware que o zera (T1), e o gerente aplicado a `core.api_key` (T2): o que a
D-41 mandou provar -- o acessor reverso, o `full_clean` e o gerente base.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.http import HttpRequest, HttpResponse
from django.test import RequestFactory

from apps.accounts.models import ApiKey
from apps.accounts.tenancy import (
    OrganizationScopeMiddleware,
    OrganizationScopeMissing,
    current_organization_id,
    organization_scope,
    set_organization_id,
)
from tests.accounts.conftest import organizacao, usuario


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


# --- o gerente aplicado a `core.api_key` (T2; o que a D-41 mandou provar) ---------------


@pytest.fixture
def duas() -> tuple[ApiKey, ApiKey]:
    """Uma chave em A e uma em B, gravadas pelo gerente base."""
    a = usuario(organizacao("org-a"), "a@a.test")
    b = usuario(organizacao("org-b"), "b@b.test")
    chave_a = ApiKey.unscoped.create(
        user=a, name="a", prefix="aaaa0001", secret_hash="0" * 64
    )
    chave_b = ApiKey.unscoped.create(
        user=b, name="b", prefix="bbbb0001", secret_hash="0" * 64
    )
    return chave_a, chave_b


@pytest.mark.django_db
def test_com_organizacao_so_as_chaves_dela(duas: tuple[ApiKey, ApiKey]) -> None:
    chave_a, chave_b = duas
    with organization_scope(chave_a.user.organization_id):
        assert list(ApiKey.objects.all()) == [chave_a]
    with organization_scope(chave_b.user.organization_id):
        assert list(ApiKey.objects.all()) == [chave_b]


@pytest.mark.django_db
def test_sem_organizacao_levanta_em_all_filter_e_create(
    duas: tuple[ApiKey, ApiKey],
) -> None:
    chave_a, _ = duas
    with pytest.raises(OrganizationScopeMissing):
        ApiKey.objects.all()
    with pytest.raises(OrganizationScopeMissing):
        ApiKey.objects.filter(prefix="aaaa0001")
    with pytest.raises(OrganizationScopeMissing):
        ApiKey.objects.create(
            user=chave_a.user, name="x", prefix="cccc0001", secret_hash="0" * 64
        )


@pytest.mark.django_db
def test_o_acessor_reverso_filtra_pelo_contexto(duas: tuple[ApiKey, ApiKey]) -> None:
    chave_a, chave_b = duas
    user_a = chave_a.user
    with organization_scope(user_a.organization_id):
        assert list(user_a.api_keys.all()) == [chave_a]
    with pytest.raises(OrganizationScopeMissing):
        list(user_a.api_keys.all())
    with organization_scope(chave_b.user.organization_id):
        assert list(user_a.api_keys.all()) == []


@pytest.mark.django_db
def test_validate_unique_ve_a_colisao_so_dentro_da_organizacao(
    duas: tuple[ApiKey, ApiKey],
) -> None:
    chave_a, chave_b = duas
    user_a = chave_a.user
    with organization_scope(user_a.organization_id):
        # o `prefix` de B: a checagem de unicidade do Django (`_perform_unique_checks`, a que
        # o `full_clean` chama) passa pelo gerente padrao e nao o ve
        de_b = ApiKey(
            user=user_a, name="x", prefix=chave_b.prefix, secret_hash="0" * 64
        )
        de_b.validate_unique()
        # o `prefix` de A: a checagem ve
        de_a = ApiKey(
            user=user_a, name="x", prefix=chave_a.prefix, secret_hash="0" * 64
        )
        with pytest.raises(ValidationError):
            de_a.validate_unique()
        # a unicidade entre organizacoes e do banco
        with pytest.raises(IntegrityError), transaction.atomic():
            de_b.save()


@pytest.mark.django_db
def test_sem_contexto_o_gerente_base_serve_ao_django(
    duas: tuple[ApiKey, ApiKey],
) -> None:
    chave_a, _ = duas
    chave_a.refresh_from_db()
    chave_a.name = "renomeada"
    chave_a.save()
    assert ApiKey.unscoped.get(pk=chave_a.pk).name == "renomeada"
    with pytest.raises(ProtectedError):
        chave_a.user.delete()


# --- a saida sem escopo so em lugar nomeado (T4)  ----------------------------------------

APPS = Path(__file__).resolve().parents[2] / "apps"
CHAMADORES_DE_UNSCOPED = {"accounts/authentication.py"}


def _chamadores_de_unscoped() -> set[str]:
    achados: set[str] = set()
    for arquivo in APPS.rglob("*.py"):
        if "migrations" in arquivo.parts:
            continue
        arvore = ast.parse(arquivo.read_text(encoding="utf-8"))
        for no in ast.walk(arvore):
            if isinstance(no, ast.Attribute) and no.attr == "unscoped":
                achados.add(arquivo.relative_to(APPS).as_posix())
    return achados


def test_unscoped_so_nos_lugares_nomeados() -> None:
    achados = _chamadores_de_unscoped()
    # contra a varredura inerte: ela acha a chamada que existe
    assert "accounts/authentication.py" in achados
    assert achados <= CHAMADORES_DE_UNSCOPED, achados - CHAMADORES_DE_UNSCOPED
