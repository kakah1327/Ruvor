"""Construtores dos testes da carteira (M2.2a), sem teste.

`conftest` nao se importa, e os testes de varios arquivos precisam dos mesmos dados: moram aqui,
no molde de `tests/accounts/risco_de_teste.py`. A organizacao e as pessoas vem de
`tests.accounts.conftest`, como nos outros testes de fora de `tests/accounts`.

`carteira` grava direto pelo ORM, sem passar pelo servico (que e da T3), sob
`organization_scope` -- os gerentes padrao das cinco tabelas levantam sem ele.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, NamedTuple

from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts import services as account_services
from apps.accounts.models import Organization, User
from apps.accounts.tenancy import organization_scope
from apps.assets.models import Asset, CollectionRun, Price
from apps.portfolios import config as portfolio_config
from apps.portfolios.models import (
    Portfolio,
    PortfolioHolding,
    PortfolioRiskResult,
    PortfolioRiskRun,
    PortfolioVersion,
)
from apps.risk.models import RiskRun
from tests.accounts.conftest import organizacao, usuario


class Pessoas(NamedTuple):
    acme: Organization
    admin: User
    member: User
    outra: Organization
    de_fora: User


def org_e_pessoas() -> Pessoas:
    """A organizacao `acme`, com uma `admin` e um `member`, e a `outra`, com uma `admin`."""
    acme = organizacao("acme")
    outra = organizacao("outra")
    return Pessoas(
        acme=acme,
        admin=usuario(acme, "admin@acme.test", role="admin"),
        member=usuario(acme, "member@acme.test", role="member"),
        outra=outra,
        de_fora=usuario(outra, "admin@outra.test", role="admin"),
    )


def acao(
    ticker: str,
    precos: Sequence[tuple[date, Decimal]],
    *,
    status: str = Asset.Status.ACTIVE,
    kind: str = Asset.Kind.STOCK,
) -> Asset:
    """O ativo do catalogo e as linhas de `silver.price` dele, todas de uma `CollectionRun`.

    Os quatro precos do dia sao o `adj_close`: a carteira so le o ajustado.
    """
    agora = timezone.now()
    asset = Asset.objects.create(
        ticker=ticker,
        kind=kind,
        name=f"{ticker} S.A.",
        trading_name=ticker,
        status=status,
        provider_symbol=f"{ticker}.SA",
        created_at=agora,
        updated_at=agora,
    )
    if precos:
        coleta = CollectionRun.objects.create(
            source="yahoo_chart",
            started_at=agora,
            finished_at=agora,
            status=CollectionRun.Status.OK,
        )
        Price.objects.bulk_create(
            Price(
                asset=asset,
                date=dia,
                open=valor,
                high=valor,
                low=valor,
                close=valor,
                adj_close=valor,
                volume=1000,
                log_return=None,
                run=coleta,
                updated_at=agora,
            )
            for dia, valor in precos
        )
    return asset


def dias_uteis(inicio: date, n: int) -> list[date]:
    """`n` dias de segunda a sexta, a partir de `inicio` (inclusive, se for dia util)."""
    dias: list[date] = []
    dia = inicio
    while len(dias) < n:
        if dia.weekday() < 5:
            dias.append(dia)
        dia += timedelta(days=1)
    return dias


def serie_longa(ticker: str, n: int = 520, inicio: date = date(2024, 1, 2)) -> Asset:
    """Um ativo com `n` pregoes em dias uteis a partir de `inicio`.

    A regra do `adj_close` do pregao `i` (0, 1, 2...) e
    `20 + d + i/100 + (i % 5)/10`, com `d` = (soma dos codigos dos caracteres do ticker) % 7:
    sempre positivo, com oscilacao (o ciclo de 5) e tendencia, e diferente de um ticker para
    outro, para que duas acoes nao deem a mesma serie.
    """
    d = Decimal(sum(ord(c) for c in ticker) % 7)
    precos = [
        (dia, Decimal(20) + d + Decimal(i) / 100 + Decimal(i % 5) / 10)
        for i, dia in enumerate(dias_uteis(inicio, n))
    ]
    return acao(ticker, precos)


def carteira(
    pessoa: User, pesos: Mapping[str, str], *, notional: str | None = None
) -> Portfolio:
    """A carteira da organizacao de `pessoa`, com a versao 1 e as posicoes `ticker -> peso`.

    Os ativos ja existem no catalogo. Grava pelo ORM, sob `organization_scope`, sem o servico.
    """
    agora = timezone.now()
    with organization_scope(pessoa.organization_id):
        portfolio = Portfolio.objects.create(
            organization_id=pessoa.organization_id,
            created_by=pessoa,
            name="Carteira de teste",
            notional=None if notional is None else Decimal(notional),
            created_at=agora,
            updated_at=agora,
        )
        versao = PortfolioVersion.objects.create(
            portfolio=portfolio, number=1, created_by=pessoa, created_at=agora
        )
        for ticker, peso in pesos.items():
            PortfolioHolding.objects.create(
                version=versao,
                asset=Asset.objects.get(ticker=ticker),
                weight=Decimal(peso),
            )
    return portfolio


def execucao(
    versao: PortfolioVersion,
    pessoa: User,
    *,
    status: str = RiskRun.Status.RUNNING,
    calculated_at: datetime | None = None,
) -> PortfolioRiskRun:
    """Uma execucao de risco da versao, com uma coleta de precos qualquer como `price_run`.

    O manifesto e de mentira (a serie e da T2): os numeros so precisam caber nas colunas.
    """
    instante = calculated_at or timezone.now()
    coleta = CollectionRun.objects.create(
        source="yahoo_chart",
        started_at=instante,
        finished_at=instante,
        status=CollectionRun.Status.OK,
    )
    with organization_scope(pessoa.organization_id):
        return PortfolioRiskRun.objects.create(
            version=versao,
            requested_by=pessoa,
            calculated_at=instante,
            finished_at=None if status == RiskRun.Status.RUNNING else instante,
            status=status,
            engine_version="",
            seed=42,
            train_window_days=252,
            first_date=date(2024, 1, 2),
            as_of_date=date(2026, 1, 2),
            session_count=520,
            train_count=252,
            test_count=267,
            requested_models=list(portfolio_config.PORTFOLIO_MODELS),
            price_run=coleta,
            series_sha256="0" * 64,
        )


def resultado(
    run: PortfolioRiskRun, model_name: str = "historical", alpha: str = "0.0500"
) -> PortfolioRiskResult:
    """Um resultado de modelo que falhou: `error` preenchido e os numeros nulos."""
    with organization_scope(run.version.portfolio.organization_id):
        return PortfolioRiskResult.objects.create(
            run=run,
            model_name=model_name,
            model_category="traditional",
            alpha=Decimal(alpha),
            hyperparameters={},
            error="RuntimeError: de teste",
        )


def sessao(user: User, *, csrf: bool = False) -> APIClient:
    """O cliente com a sessao de `user`, por `force_login` -- nunca `force_authenticate`, que
    deixa o pedido sem a organizacao no contexto."""
    cliente = APIClient(enforce_csrf_checks=csrf)
    cliente.force_login(user)
    return cliente


def chave(user: User) -> APIClient:
    """O cliente com uma chave de leitura de `user`, pelo `Bearer`."""
    segredo = account_services.create_api_key(user, name="leitura", ip=None)[1]
    cliente = APIClient()
    cliente.credentials(HTTP_AUTHORIZATION=f"Bearer {segredo}")
    return cliente


def erro(resposta: Any, status: int, codigo: str) -> dict[str, Any]:
    """O corpo de erro da D-86, conferido na forma; devolve o corpo inteiro."""
    assert resposta.status_code == status, resposta.content
    assert resposta["Content-Type"] == "application/json"
    corpo: dict[str, Any] = resposta.json()
    assert set(corpo) == {"error"}
    assert set(corpo["error"]) == {"code", "message", "details"}
    assert corpo["error"]["code"] == codigo
    return corpo
