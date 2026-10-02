"""M2.2a, T1: o filtro automatico por organizacao nas cinco tabelas (RF-18; V-10, a parte das
tabelas).

No molde de `tests/accounts/test_tenancy.py`, o que a D-41 manda provar em cada tabela privada:
sem contexto o gerente padrao levanta; com a outra organizacao, vazio; o acessor reverso segue o
contexto; o gerente base serve ao Django sem contexto (`refresh_from_db`, o `save` da criacao); o
`full_clean` ve o unico com o contexto posto; e o `Meta.base_manager_name` e o `unscoped`.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, NamedTuple

import pytest
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.db import models
from django.db.models import QuerySet
from django.utils import timezone

from apps.accounts.tenancy import (
    OrganizationScopedManager,
    OrganizationScopeMissing,
    organization_scope,
)
from apps.assets.models import Asset
from apps.portfolios.models import (
    Portfolio,
    PortfolioHolding,
    PortfolioRiskResult,
    PortfolioRiskRun,
    PortfolioVersion,
)
from tests.portfolios.dados import (
    Pessoas,
    acao,
    carteira,
    execucao,
    org_e_pessoas,
    resultado,
)

pytestmark = pytest.mark.django_db

MODELOS: list[type[models.Model]] = [
    Portfolio,
    PortfolioVersion,
    PortfolioHolding,
    PortfolioRiskRun,
    PortfolioRiskResult,
]


class Linhas(NamedTuple):
    pessoas: Pessoas
    portfolio: Portfolio
    versao: PortfolioVersion
    posicao: PortfolioHolding
    run: PortfolioRiskRun
    resultado: PortfolioRiskResult

    def de(self, modelo: type[models.Model]) -> models.Model:
        return {
            Portfolio: self.portfolio,
            PortfolioVersion: self.versao,
            PortfolioHolding: self.posicao,
            PortfolioRiskRun: self.run,
            PortfolioRiskResult: self.resultado,
        }[modelo]


@pytest.fixture
def linhas() -> Linhas:
    """Uma linha de cada tabela na `acme`; a `outra` nao tem nenhuma."""
    pessoas = org_e_pessoas()
    acao("PETR4", [])
    portfolio = carteira(pessoas.admin, {"PETR4": "100.00"})
    versao = PortfolioVersion.unscoped.get(portfolio=portfolio)
    run = execucao(versao, pessoas.admin)
    return Linhas(
        pessoas=pessoas,
        portfolio=portfolio,
        versao=versao,
        posicao=PortfolioHolding.unscoped.get(version=versao),
        run=run,
        resultado=resultado(run),
    )


@pytest.mark.parametrize("modelo", MODELOS, ids=lambda m: m.__name__)
def test_v10_sem_contexto_o_gerente_padrao_levanta(
    linhas: Linhas, modelo: type[models.Model]
) -> None:
    with pytest.raises(OrganizationScopeMissing):
        modelo._default_manager.all()
    with pytest.raises(OrganizationScopeMissing):
        modelo._default_manager.filter(pk=linhas.de(modelo).pk)


@pytest.mark.parametrize("modelo", MODELOS, ids=lambda m: m.__name__)
def test_v10_com_a_organizacao_so_as_linhas_dela(
    linhas: Linhas, modelo: type[models.Model]
) -> None:
    with organization_scope(linhas.pessoas.acme.pk):
        assert list(modelo._default_manager.all()) == [linhas.de(modelo)]
    with organization_scope(linhas.pessoas.outra.pk):
        assert list(modelo._default_manager.all()) == []


@pytest.mark.parametrize("modelo", MODELOS, ids=lambda m: m.__name__)
def test_v10_o_gerente_base_e_o_unscoped(modelo: type[models.Model]) -> None:
    assert modelo._meta.base_manager_name == "unscoped"
    assert not isinstance(modelo._meta.base_manager, OrganizationScopedManager)
    assert isinstance(modelo._meta.default_manager, OrganizationScopedManager)


@pytest.mark.parametrize("modelo", MODELOS, ids=lambda m: m.__name__)
def test_v10_sem_contexto_o_refresh_from_db_passa(
    linhas: Linhas, modelo: type[models.Model]
) -> None:
    linhas.de(modelo).refresh_from_db()


def test_v10_os_acessores_reversos_seguem_o_contexto(linhas: Linhas) -> None:
    reversos: list[tuple[Callable[[], QuerySet[Any]], models.Model]] = [
        (lambda: linhas.portfolio.versions.all(), linhas.versao),
        (lambda: linhas.versao.holdings.all(), linhas.posicao),
        (lambda: linhas.versao.risk_runs.all(), linhas.run),
        (lambda: linhas.run.results.all(), linhas.resultado),
    ]
    for consulta, esperado in reversos:
        with organization_scope(linhas.pessoas.acme.pk):
            assert list(consulta()) == [esperado]
        with organization_scope(linhas.pessoas.outra.pk):
            assert list(consulta()) == []
        with pytest.raises(OrganizationScopeMissing):
            list(consulta())


def test_v10_sem_contexto_o_save_da_criacao_passa_nas_cinco(linhas: Linhas) -> None:
    agora = timezone.now()
    pessoas = linhas.pessoas
    portfolio = Portfolio(
        organization=pessoas.outra,
        created_by=pessoas.de_fora,
        name="Sem contexto",
        created_at=agora,
        updated_at=agora,
    )
    portfolio.save()
    versao = PortfolioVersion(
        portfolio=portfolio, number=1, created_by=pessoas.de_fora, created_at=agora
    )
    versao.save()
    PortfolioHolding(
        version=versao, asset=Asset.objects.get(ticker="PETR4"), weight=100
    ).save()
    run = PortfolioRiskRun(
        **{
            campo.name: getattr(linhas.run, campo.name)
            for campo in PortfolioRiskRun._meta.concrete_fields
            if campo.name not in {"id", "version", "requested_by"}
        },
        version=versao,
        requested_by=pessoas.de_fora,
    )
    run.save()
    PortfolioRiskResult(
        run=run,
        model_name="historical",
        model_category="traditional",
        alpha="0.0500",
        hyperparameters={},
    ).save()
    with organization_scope(pessoas.outra.pk):
        assert PortfolioRiskResult.objects.get().run == run
        assert PortfolioHolding.objects.get().version == versao


def test_v10_com_contexto_o_full_clean_acusa_a_versao_repetida(linhas: Linhas) -> None:
    repetida = PortfolioVersion(
        portfolio=linhas.portfolio,
        number=1,
        created_by=linhas.pessoas.admin,
        created_at=timezone.now(),
    )
    with organization_scope(linhas.pessoas.acme.pk):
        with pytest.raises(ValidationError) as erro:
            repetida.full_clean()
    assert [e.code for e in erro.value.error_dict[NON_FIELD_ERRORS]] == [
        "unique_together"
    ]


def test_v10_com_contexto_o_full_clean_acusa_a_posicao_repetida(
    linhas: Linhas,
) -> None:
    repetida = PortfolioHolding(
        version=linhas.versao,
        asset=Asset.objects.get(ticker="PETR4"),
        weight=10,
    )
    with organization_scope(linhas.pessoas.acme.pk):
        with pytest.raises(ValidationError) as erro:
            repetida.full_clean()
    assert [e.code for e in erro.value.error_dict[NON_FIELD_ERRORS]] == [
        "unique_together"
    ]
